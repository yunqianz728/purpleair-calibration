"""
ERA5 Data Reader
================

Reads ERA5 NetCDF data from local files and interpolates to sensor locations.

Author: Yunqian Zhang, Lu Liang
"""

import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
import os

warnings.filterwarnings('ignore')

# ERA5数据路径（本地NetCDF文件）
ERA5_DATA_DIR = "/Users/yunqianzhang/Desktop/PA/气象数据"

# Zenodo配置
ZENODO_RECORD_ID = os.getenv('ZENODO_RECORD_ID', 'XXXXXXX')  # 从环境变量读取
USE_ZENODO = os.getenv('USE_ZENODO', 'false').lower() == 'true'


class ERA5Reader:
    """ERA5 NetCDF数据读取器（支持本地文件和Zenodo自动下载）"""

    def __init__(self, data_dir=ERA5_DATA_DIR, use_zenodo=USE_ZENODO,
                 zenodo_record_id=ZENODO_RECORD_ID):
        """
        初始化ERA5读取器

        Parameters:
        -----------
        data_dir : str
            ERA5 NetCDF文件所在目录（本地模式）
        use_zenodo : bool
            是否使用Zenodo自动下载（云端部署时）
        zenodo_record_id : str
            Zenodo记录ID
        """
        self.data_dir = Path(data_dir) if data_dir else None
        self.use_zenodo = use_zenodo
        self.zenodo_record_id = zenodo_record_id
        self.cache = {}  # 缓存已加载的数据集

        # 如果启用Zenodo，导入下载器
        if self.use_zenodo:
            try:
                from .zenodo_downloader import ZenodoERA5Downloader
                self.downloader = ZenodoERA5Downloader(zenodo_record_id=zenodo_record_id)
                print(f"✅ Zenodo downloader initialized (Record ID: {zenodo_record_id})")
            except ImportError:
                print("⚠️ zenodo_downloader not found, falling back to local files")
                self.use_zenodo = False

    def get_era5_data(self, timestamp, latitude, longitude):
        """
        获取指定时间和位置的ERA5数据

        Parameters:
        -----------
        timestamp : datetime or str
            时间点
        latitude : float
            纬度（-90到90）
        longitude : float
            经度（-180到180或0到360）

        Returns:
        --------
        dict : ERA5变量字典
            包含 sshf, ssrd, strd, tp, u10, v10
        """
        # 转换timestamp
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)

        # 确定NC文件
        year_month = timestamp.strftime('%Y-%m')

        # 优先使用本地文件，如果不存在则尝试Zenodo
        nc_file = None
        if self.data_dir and self.data_dir.exists():
            local_file = self.data_dir / f"{year_month}.nc"
            if local_file.exists():
                nc_file = local_file
                # print(f"📂 Using local file: {year_month}.nc")

        # 如果本地文件不存在且启用了Zenodo，从Zenodo下载
        if nc_file is None and self.use_zenodo:
            try:
                print(f"📥 Downloading {year_month}.nc from Zenodo...")
                nc_file = self.downloader.download_file(year_month, show_progress=False)
                print(f"✅ Downloaded from Zenodo: {year_month}.nc")
            except Exception as e:
                raise FileNotFoundError(
                    f"ERA5 data not available for {year_month}.\n"
                    f"Local file not found and Zenodo download failed: {str(e)}"
                )

        # 如果两种方式都失败了
        if nc_file is None:
            raise FileNotFoundError(
                f"ERA5 data not found for {year_month}.\n"
                f"Local directory: {self.data_dir}\n"
                f"Zenodo enabled: {self.use_zenodo}\n"
                f"Please ensure data is available locally or enable Zenodo download."
            )

        # 加载数据集（使用缓存）
        if year_month not in self.cache:
            try:
                self.cache[year_month] = xr.open_dataset(nc_file)
            except Exception as e:
                raise IOError(f"Failed to load ERA5 data from {nc_file}: {str(e)}")

        ds = self.cache[year_month]

        # 处理经度（ERA5使用0-360度）
        if longitude < 0:
            longitude += 360

        try:
            # 时间插值
            era5_data = ds.sel(
                latitude=latitude,
                longitude=longitude,
                valid_time=timestamp,
                method='nearest'
            )

            # 提取变量
            result = {
                'sshf': float(era5_data['sshf'].values) if 'sshf' in era5_data else 0.0,
                'ssrd': float(era5_data['ssrd'].values) if 'ssrd' in era5_data else 0.0,
                'strd': float(era5_data['strd'].values) if 'strd' in era5_data else 0.0,
                'tp': float(era5_data['tp'].values) if 'tp' in era5_data else 0.0,
            }

            # 计算风速（如果有u10和v10）
            if 'u10' in era5_data and 'v10' in era5_data:
                u10 = float(era5_data['u10'].values)
                v10 = float(era5_data['v10'].values)
                result['u10'] = u10
                result['v10'] = v10
                result['wind_speed'] = np.sqrt(u10**2 + v10**2)
                result['wind_direction'] = np.arctan2(v10, u10) * 180 / np.pi
            else:
                result['u10'] = 0.0
                result['v10'] = 0.0
                result['wind_speed'] = 0.0
                result['wind_direction'] = 0.0

            return result

        except Exception as e:
            raise ValueError(
                f"Failed to extract ERA5 data for time={timestamp}, "
                f"lat={latitude}, lon={longitude}: {str(e)}"
            )

    def get_batch_era5_data(self, df):
        """
        批量获取ERA5数据

        Parameters:
        -----------
        df : pandas.DataFrame
            包含 timestamp, latitude, longitude 列的数据框

        Returns:
        --------
        pandas.DataFrame : 添加了ERA5数据的数据框
        """
        era5_results = []

        for idx, row in df.iterrows():
            try:
                era5_data = self.get_era5_data(
                    row['timestamp'],
                    row['latitude'],
                    row['longitude']
                )
                era5_results.append(era5_data)
            except Exception as e:
                print(f"Warning: Failed to get ERA5 data for row {idx}: {str(e)}")
                # 使用默认值
                era5_results.append({
                    'sshf': 0.0, 'ssrd': 0.0, 'strd': 0.0, 'tp': 0.0,
                    'u10': 0.0, 'v10': 0.0, 'wind_speed': 0.0, 'wind_direction': 0.0
                })

        # 合并到原始数据框
        era5_df = pd.DataFrame(era5_results)
        result_df = pd.concat([df.reset_index(drop=True), era5_df], axis=1)

        return result_df

    def close(self):
        """关闭所有缓存的数据集"""
        for ds in self.cache.values():
            ds.close()
        self.cache = {}


# 辅助函数
def load_era5_for_dataframe(df, data_dir=ERA5_DATA_DIR):
    """
    便捷函数：为DataFrame添加ERA5数据

    Parameters:
    -----------
    df : pandas.DataFrame
        必须包含 timestamp, latitude, longitude 列
    data_dir : str
        ERA5数据目录

    Returns:
    --------
    pandas.DataFrame : 添加了ERA5变量的数据框
    """
    reader = ERA5Reader(data_dir)
    result = reader.get_batch_era5_data(df)
    reader.close()
    return result


if __name__ == "__main__":
    # 测试代码
    print("ERA5 Reader - 测试")
    print("=" * 50)

    # 创建测试数据
    test_df = pd.DataFrame({
        'timestamp': ['2024-01-15 12:00:00', '2024-01-15 13:00:00'],
        'latitude': [37.7749, 37.7749],
        'longitude': [-122.4194, -122.4194]
    })

    print("\n输入数据:")
    print(test_df)

    # 加载ERA5数据
    try:
        result = load_era5_for_dataframe(test_df)
        print("\n结果（包含ERA5数据）:")
        print(result[['timestamp', 'sshf', 'ssrd', 'strd', 'tp']])
        print("\n✅ ERA5数据加载成功！")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
