"""
Model Predictor for PurpleAir Temperature Calibration
======================================================

Loads trained XGBoost models and performs temperature-stratified prediction.

Models:
- Cold model: T < 10°C
- Normal model: 10°C ≤ T ≤ 30°C
- Hot model: T > 30°C

Author: Yunqian Zhang, Lu Liang
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# 模型文件路径
MODEL_DIR = Path(__file__).parent.parent / "models"

MODELS = {
    'cold': MODEL_DIR / "station_temperature_cold_xgboost.pkl",
    'normal': MODEL_DIR / "station_temperature_normal_xgboost.pkl",
    'hot': MODEL_DIR / "station_temperature_hot_xgboost.pkl"
}


class TemperatureCalibrator:
    """温度分层校准器"""

    def __init__(self):
        """加载所有模型"""
        self.models = {}
        self._load_models()

    def _load_models(self):
        """加载XGBoost模型"""
        for model_name, model_path in MODELS.items():
            if not model_path.exists():
                raise FileNotFoundError(f"Model not found: {model_path}")

            try:
                with open(model_path, 'rb') as f:
                    self.models[model_name] = pickle.load(f)
                print(f"✅ Loaded {model_name} model from {model_path.name}")
            except Exception as e:
                raise IOError(f"Failed to load {model_name} model: {str(e)}")

    @staticmethod
    def determine_temperature_regime(temperature):
        """
        确定温度范围

        Parameters:
        -----------
        temperature : float
            传感器温度（摄氏度）

        Returns:
        --------
        str : 'cold', 'normal', 或 'hot'
        """
        if temperature < 10:
            return 'cold'
        elif temperature > 30:
            return 'hot'
        else:
            return 'normal'

    def calibrate(self, df_features, feature_list):
        """
        校准温度

        Parameters:
        -----------
        df_features : pandas.DataFrame
            包含所有63个特征的数据框
        feature_list : list
            模型所需的特征列表（63个特征）

        Returns:
        --------
        pandas.DataFrame : 添加了calibrated_temperature列的数据框
        """
        df_result = df_features.copy()
        calibrated_temps = []

        for idx, row in df_result.iterrows():
            sensor_temp = row['sensor temperature']

            # 确定使用哪个模型
            regime = self.determine_temperature_regime(sensor_temp)

            # 选择模型
            model = self.models[regime]

            # 准备特征
            try:
                features = row[feature_list].values.reshape(1, -1)

                # 预测校准后的温度
                calibrated_temp = model.predict(features)[0]

                calibrated_temps.append(calibrated_temp)

            except Exception as e:
                print(f"Warning: Prediction failed for row {idx}: {str(e)}")
                # 如果预测失败，使用原始温度
                calibrated_temps.append(sensor_temp)

        # 添加校准后的温度列
        df_result['calibrated_temperature'] = calibrated_temps

        # 计算校准修正量
        df_result['calibration_correction'] = df_result['sensor temperature'] - df_result['calibrated_temperature']

        # 添加温度范围标签
        df_result['temperature_regime'] = df_result['sensor temperature'].apply(
            self.determine_temperature_regime
        )

        return df_result

    def get_model_info(self):
        """返回模型信息"""
        info = {}
        for model_name, model in self.models.items():
            info[model_name] = {
                'type': type(model).__name__,
                'n_features': model.n_features_in_ if hasattr(model, 'n_features_in_') else 'Unknown'
            }
        return info


# 便捷函数
def calibrate_temperature(df_features, feature_list):
    """
    便捷函数：校准温度

    Parameters:
    -----------
    df_features : pandas.DataFrame
        包含所有特征的数据框
    feature_list : list
        特征列表

    Returns:
    --------
    pandas.DataFrame : 校准后的数据
    """
    calibrator = TemperatureCalibrator()
    return calibrator.calibrate(df_features, feature_list)


if __name__ == "__main__":
    # 测试代码
    print("Model Predictor - 测试")
    print("=" * 50)

    # 创建测试数据
    from feature_engineering import FeatureEngineer

    test_df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-15 10:00', periods=10, freq='h'),
        'temperature': [8, 12, 18, 25, 32, 28, 22, 15, 10, 5],  # 覆盖cold/normal/hot
        'humidity': [50] * 10,
        'latitude': [37.7749] * 10,
        'longitude': [-122.4194] * 10,
        'sshf': [100] * 10,
        'ssrd': [500] * 10,
        'strd': [300] * 10,
        'tp': [0] * 10,
        'u10': [2] * 10,
        'v10': [1] * 10,
    })

    print("\n输入数据（原始传感器温度）:")
    print(test_df[['timestamp', 'temperature']].head())

    # 特征工程
    engineer = FeatureEngineer()
    df_features = engineer.engineer_all_features(test_df)
    feature_list = engineer.get_feature_list()

    print(f"\n生成特征: {len(feature_list)} 个")

    # 校准
    calibrator = TemperatureCalibrator()
    result = calibrator.calibrate(df_features, feature_list)

    print("\n校准结果:")
    print(result[['timestamp', 'sensor temperature', 'calibrated_temperature',
                  'calibration_correction', 'temperature_regime']].head(10))

    print("\n✅ 模型预测测试完成！")
