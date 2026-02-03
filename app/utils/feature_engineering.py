"""
Complete Feature Engineering for PurpleAir Temperature Calibration
===================================================================

Implements all 63 features used in the Temporal-TempStrat model.

Features:
- 27 basic features
- 11 lagged features
- 4 change rate features
- 15 statistical features (rolling windows)
- 4 wind features
- 2 classification features

Author: Yunqian Zhang, Lu Liang
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


class FeatureEngineer:
    """完整的特征工程器 - 63个特征"""

    @staticmethod
    def calculate_dewpoint(temperature_c, relative_humidity):
        """
        计算露点温度（Magnus-Tetens公式）

        Parameters:
        -----------
        temperature_c : float or array
            温度（摄氏度）
        relative_humidity : float or array
            相对湿度（0-100）

        Returns:
        --------
        float or array : 露点温度（摄氏度）
        """
        a = 17.27
        b = 237.7

        alpha = ((a * temperature_c) / (b + temperature_c)) + np.log(relative_humidity / 100.0)
        dewpoint = (b * alpha) / (a - alpha)

        return dewpoint

    @staticmethod
    def calculate_vpd(temperature_c, relative_humidity):
        """
        计算蒸汽压差（VPD）

        Parameters:
        -----------
        temperature_c : float or array
            温度（摄氏度）
        relative_humidity : float or array
            相对湿度（0-100）

        Returns:
        --------
        float or array : VPD（kPa）
        """
        # 饱和蒸汽压（kPa）
        es = 0.6108 * np.exp((17.27 * temperature_c) / (temperature_c + 237.3))

        # 实际蒸汽压
        ea = es * (relative_humidity / 100.0)

        # VPD
        vpd = es - ea

        return vpd

    def engineer_all_features(self, df):
        """
        计算所有63个特征

        Parameters:
        -----------
        df : pandas.DataFrame
            输入数据，必须包含：
            - timestamp: 时间戳
            - temperature: 传感器温度（华氏或摄氏）
            - humidity: 相对湿度
            - latitude: 纬度
            - longitude: 经度
            - sshf, ssrd, strd, tp: ERA5数据（已通过era5_reader获取）

        Returns:
        --------
        pandas.DataFrame : 包含所有63个特征的数据框
        """
        df = df.copy()

        # 确保timestamp是datetime类型
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # ========================================
        # 1. 基础特征（27个）
        # ========================================

        # 时间特征
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.day
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_month'] = df['timestamp'].dt.day

        # 周期性编码
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['month_sin'] = np.sin(2 * np.pi * (df['month'] - 1) / 12)
        df['month_cos'] = np.cos(2 * np.pi * (df['month'] - 1) / 12)

        # 传感器数据重命名
        if 'temperature' in df.columns:
            df['sensor temperature'] = df['temperature']

        # 确保温度是摄氏度
        if df['sensor temperature'].mean() > 50:  # 可能是华氏度
            df['sensor temperature'] = (df['sensor temperature'] - 32) * 5/9

        # 位置特征
        df['sensor_lat'] = df['latitude']
        df['sensor_lon'] = df['longitude']

        # 默认值（如果没有提供）
        if 'elevation' not in df.columns:
            df['elevation_sensor'] = 0  # 可以从DEM获取，暂时默认0
        else:
            df['elevation_sensor'] = df['elevation']

        if 'life' not in df.columns:
            df['life'] = 365  # 假设传感器已运行1年

        if 'tcc' not in df.columns:
            df['sensor_tcc'] = 0  # 树冠覆盖度，默认0
        else:
            df['sensor_tcc'] = df['tcc']

        # ERA5数据（已通过era5_reader获取）
        # sshf, ssrd, strd, tp 应该已存在

        # 交互特征
        df['humidity_squared'] = df['humidity'] ** 2
        df['temp_squared_sensor'] = df['sensor temperature'] ** 2
        df['temp_humidity_product_sensor'] = df['sensor temperature'] * df['humidity']
        df['temp_life_interaction_sensor'] = df['sensor temperature'] * df['life']

        # 衍生气象特征
        df['dewpoint_sensor'] = self.calculate_dewpoint(
            df['sensor temperature'],
            df['humidity']
        )
        df['dewpoint_depression_sensor'] = df['sensor temperature'] - df['dewpoint_sensor']
        df['vapor_pressure_deficit_sensor'] = self.calculate_vpd(
            df['sensor temperature'],
            df['humidity']
        )

        # 辐射特征
        if 'ssrd' in df.columns:
            df['diurnal_radiation'] = df['ssrd'] * np.abs(np.sin(2 * np.pi * df['hour'] / 24))
        else:
            df['diurnal_radiation'] = 0

        # 极地日夜特征（高纬度）
        df['polar_day_night'] = ((df['sensor_lat'].abs() > 60) &
                                 ((df['month'].isin([6,7,8]) & (df['sensor_lat'] > 0)) |
                                  (df['month'].isin([12,1,2]) & (df['sensor_lat'] < 0)))).astype(int)

        # 风速特征（如果ERA5中有）
        if 'u10' not in df.columns:
            df['u10'] = 0
            df['v10'] = 0
            df['wind_speed'] = 0
            df['wind_direction'] = 0

        # ========================================
        # 2. 滞后特征（11个）
        # ========================================

        # 假设数据是时间排序的
        df = df.sort_values('timestamp').reset_index(drop=True)

        # 温度滞后（1-6小时）
        for lag in range(1, 7):
            df[f'sensor_temp_{lag}h_ago'] = df['sensor temperature'].shift(lag)

        # 湿度滞后（1-3小时）
        for lag in range(1, 4):
            df[f'humidity_{lag}h_ago'] = df['humidity'].shift(lag)

        # 辐射滞后（1-2小时）
        if 'ssrd' in df.columns:
            df['ssrd_1h_ago'] = df['ssrd'].shift(1)
            df['ssrd_2h_ago'] = df['ssrd'].shift(2)
        else:
            df['ssrd_1h_ago'] = 0
            df['ssrd_2h_ago'] = 0

        # ========================================
        # 3. 变化率特征（4个）
        # ========================================

        df['temp_change_1h'] = df['sensor temperature'] - df['sensor_temp_1h_ago']
        df['temp_change_2h'] = df['sensor temperature'] - df['sensor_temp_2h_ago']
        df['temp_change_3h'] = df['sensor temperature'] - df['sensor_temp_3h_ago']

        # 加速度（二阶导数）
        df['temp_acceleration'] = df['temp_change_1h'] - df['temp_change_1h'].shift(1)

        # ========================================
        # 4. 统计特征（15个）- 滚动窗口
        # ========================================

        # 滚动平均
        df['temp_ma_3h'] = df['sensor temperature'].rolling(window=3, min_periods=1).mean()
        df['temp_ma_6h'] = df['sensor temperature'].rolling(window=6, min_periods=1).mean()
        df['temp_ma_12h'] = df['sensor temperature'].rolling(window=12, min_periods=1).mean()

        # 滚动标准差
        df['temp_std_3h'] = df['sensor temperature'].rolling(window=3, min_periods=1).std().fillna(0)
        df['temp_std_6h'] = df['sensor temperature'].rolling(window=6, min_periods=1).std().fillna(0)
        df['temp_std_12h'] = df['sensor temperature'].rolling(window=12, min_periods=1).std().fillna(0)

        # 滚动极差
        df['temp_range_3h'] = (df['sensor temperature'].rolling(window=3, min_periods=1).max() -
                               df['sensor temperature'].rolling(window=3, min_periods=1).min())
        df['temp_range_6h'] = (df['sensor temperature'].rolling(window=6, min_periods=1).max() -
                               df['sensor temperature'].rolling(window=6, min_periods=1).min())

        # 温度趋势（线性回归斜率近似）
        df['temp_trend_3h'] = df['temp_change_1h'].rolling(window=3, min_periods=1).mean()
        df['temp_trend_6h'] = df['temp_change_1h'].rolling(window=6, min_periods=1).mean()

        # 累积辐射
        if 'ssrd' in df.columns:
            df['ssrd_sum_3h'] = df['ssrd'].rolling(window=3, min_periods=1).sum()
            df['ssrd_sum_6h'] = df['ssrd'].rolling(window=6, min_periods=1).sum()
            df['ssrd_change'] = df['ssrd'] - df['ssrd_1h_ago']
        else:
            df['ssrd_sum_3h'] = 0
            df['ssrd_sum_6h'] = 0
            df['ssrd_change'] = 0

        # 热浪/寒潮计数器
        threshold_hot = 30  # 摄氏度
        threshold_cold = 10

        df['hot_streak'] = (df['sensor temperature'] > threshold_hot).astype(int)
        df['hot_streak'] = df['hot_streak'].groupby((df['hot_streak'] != df['hot_streak'].shift()).cumsum()).cumsum()

        df['cold_streak'] = (df['sensor temperature'] < threshold_cold).astype(int)
        df['cold_streak'] = df['cold_streak'].groupby((df['cold_streak'] != df['cold_streak'].shift()).cumsum()).cumsum()

        # ========================================
        # 5. 分类特征（2个）
        # ========================================

        df['is_hot'] = (df['sensor temperature'] > 30).astype(int)
        df['is_cold'] = (df['sensor temperature'] < 10).astype(int)

        # 填充NaN（滞后和滚动特征会产生NaN）
        # 用前向填充，如果还有NaN则用0填充
        df = df.fillna(method='ffill').fillna(0)

        return df

    @staticmethod
    def get_feature_list():
        """返回完整的63个特征列表（用于模型预测）"""
        features = [
            # 基础特征（27个）
            'day', 'elevation_sensor', 'humidity', 'life', 'sensor_lat', 'sensor_lon',
            'sensor_tcc', 'sensor temperature', 'year', 'sshf', 'ssrd', 'strd', 'tp',
            'humidity_squared', 'temp_squared_sensor', 'temp_humidity_product_sensor',
            'temp_life_interaction_sensor', 'dewpoint_sensor', 'dewpoint_depression_sensor',
            'vapor_pressure_deficit_sensor', 'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
            'diurnal_radiation', 'polar_day_night', 'day_of_month',

            # 滞后特征（11个）
            'sensor_temp_1h_ago', 'sensor_temp_2h_ago', 'sensor_temp_3h_ago',
            'sensor_temp_4h_ago', 'sensor_temp_5h_ago', 'sensor_temp_6h_ago',
            'humidity_1h_ago', 'humidity_2h_ago', 'humidity_3h_ago',
            'ssrd_1h_ago', 'ssrd_2h_ago',

            # 变化率特征（4个）
            'temp_change_1h', 'temp_change_2h', 'temp_change_3h', 'temp_acceleration',

            # 统计特征（15个）
            'temp_ma_3h', 'temp_ma_6h', 'temp_ma_12h',
            'temp_std_3h', 'temp_std_6h', 'temp_std_12h',
            'temp_range_3h', 'temp_range_6h',
            'temp_trend_3h', 'temp_trend_6h',
            'ssrd_sum_3h', 'ssrd_sum_6h', 'ssrd_change',
            'hot_streak', 'cold_streak',

            # 风速特征（4个）
            'u10', 'v10', 'wind_speed', 'wind_direction',

            # 分类特征（2个）
            'is_hot', 'is_cold'
        ]

        return features


if __name__ == "__main__":
    # 测试代码
    print("Feature Engineering - 测试")
    print("=" * 50)

    # 创建测试数据
    test_df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-15 10:00', periods=24, freq='h'),
        'temperature': np.random.uniform(20, 30, 24),  # 摄氏度
        'humidity': np.random.uniform(40, 60, 24),
        'latitude': [37.7749] * 24,
        'longitude': [-122.4194] * 24,
        'sshf': np.random.uniform(50, 150, 24),
        'ssrd': np.random.uniform(0, 800, 24),
        'strd': np.random.uniform(200, 400, 24),
        'tp': np.random.uniform(0, 5, 24),
        'u10': np.random.uniform(-5, 5, 24),
        'v10': np.random.uniform(-5, 5, 24),
    })

    print(f"\n输入数据: {len(test_df)} 行")
    print(test_df.head())

    # 特征工程
    engineer = FeatureEngineer()
    result = engineer.engineer_all_features(test_df)

    feature_list = engineer.get_feature_list()
    print(f"\n特征总数: {len(feature_list)}")
    print(f"\n前10个特征:")
    print(feature_list[:10])

    print(f"\n结果数据: {len(result)} 行 × {len(result.columns)} 列")
    print(f"\n生成的特征（前20个）:")
    print(result[feature_list[:20]].head())

    print("\n✅ 特征工程测试完成！")
