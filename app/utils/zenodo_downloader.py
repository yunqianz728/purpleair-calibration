"""
Zenodo ERA5 Data Downloader
============================

Automatically downloads ERA5 NetCDF files from Zenodo as needed.

Author: Yunqian Zhang, Lu Liang
"""

import os
import requests
from pathlib import Path
import hashlib
from tqdm import tqdm

# Zenodo record ID（你需要在上传后替换这个ID）
ZENODO_RECORD_ID = "XXXXXXX"  # 替换为你的Zenodo record ID

# ERA5文件在Zenodo上的URL模板
ZENODO_BASE_URL = f"https://zenodo.org/record/{ZENODO_RECORD_ID}/files/"

# 本地缓存目录
CACHE_DIR = Path("/tmp/era5_cache")  # Streamlit Cloud临时存储


class ZenodoERA5Downloader:
    """从Zenodo自动下载ERA5数据"""

    def __init__(self, cache_dir=CACHE_DIR, zenodo_record_id=ZENODO_RECORD_ID):
        """
        初始化下载器

        Parameters:
        -----------
        cache_dir : str or Path
            本地缓存目录
        zenodo_record_id : str
            Zenodo记录ID
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.zenodo_record_id = zenodo_record_id
        self.base_url = f"https://zenodo.org/record/{zenodo_record_id}/files/"

    def get_file_url(self, year_month):
        """
        获取指定年月的ERA5文件URL

        Parameters:
        -----------
        year_month : str
            格式：'YYYY-MM'，如 '2024-01'

        Returns:
        --------
        str : Zenodo下载URL
        """
        filename = f"{year_month}.nc"
        return f"{self.base_url}{filename}"

    def download_file(self, year_month, force=False, show_progress=True):
        """
        下载指定年月的ERA5文件

        Parameters:
        -----------
        year_month : str
            格式：'YYYY-MM'
        force : bool
            是否强制重新下载（即使缓存存在）
        show_progress : bool
            是否显示下载进度条

        Returns:
        --------
        Path : 本地文件路径
        """
        filename = f"{year_month}.nc"
        local_path = self.cache_dir / filename

        # 检查缓存
        if local_path.exists() and not force:
            print(f"✅ Using cached file: {filename}")
            return local_path

        # 下载文件
        url = self.get_file_url(year_month)
        print(f"📥 Downloading {filename} from Zenodo...")
        print(f"   URL: {url}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))

            # 下载并显示进度
            with open(local_path, 'wb') as f:
                if show_progress and total_size > 0:
                    # 使用tqdm显示进度条
                    with tqdm(total=total_size, unit='B', unit_scale=True,
                             desc=filename) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    # 不显示进度条
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            print(f"✅ Downloaded: {filename} ({total_size / 1024 / 1024:.1f} MB)")
            return local_path

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(
                    f"ERA5 file not found on Zenodo: {filename}\n"
                    f"Available range: 2022-01 to 2024-12\n"
                    f"Check Zenodo record: {self.zenodo_record_id}"
                )
            else:
                raise IOError(f"Failed to download {filename}: {str(e)}")
        except Exception as e:
            raise IOError(f"Download error for {filename}: {str(e)}")

    def download_multiple(self, year_months, show_progress=True):
        """
        下载多个月份的数据

        Parameters:
        -----------
        year_months : list of str
            年月列表，如 ['2024-01', '2024-02']
        show_progress : bool
            是否显示进度

        Returns:
        --------
        dict : {year_month: local_path}
        """
        results = {}
        for ym in year_months:
            try:
                path = self.download_file(ym, show_progress=show_progress)
                results[ym] = path
            except Exception as e:
                print(f"⚠️ Failed to download {ym}: {str(e)}")
                results[ym] = None

        return results

    def clear_cache(self, keep_recent=0):
        """
        清理缓存

        Parameters:
        -----------
        keep_recent : int
            保留最近N个文件，0表示全部删除
        """
        files = sorted(self.cache_dir.glob("*.nc"), key=os.path.getmtime, reverse=True)

        if keep_recent > 0:
            files_to_delete = files[keep_recent:]
        else:
            files_to_delete = files

        for f in files_to_delete:
            f.unlink()
            print(f"🗑️ Deleted cached file: {f.name}")

        if files_to_delete:
            print(f"✅ Cleared {len(files_to_delete)} cached files")

    def get_cache_info(self):
        """获取缓存信息"""
        files = list(self.cache_dir.glob("*.nc"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            'num_files': len(files),
            'total_size_mb': total_size / 1024 / 1024,
            'files': [f.name for f in sorted(files)]
        }


# 便捷函数
def download_era5_for_months(year_months, cache_dir=CACHE_DIR):
    """
    便捷函数：下载指定月份的ERA5数据

    Parameters:
    -----------
    year_months : list of str
        年月列表，如 ['2024-01', '2024-02']
    cache_dir : str or Path
        缓存目录

    Returns:
    --------
    dict : {year_month: local_path}
    """
    downloader = ZenodoERA5Downloader(cache_dir=cache_dir)
    return downloader.download_multiple(year_months)


if __name__ == "__main__":
    # 测试代码
    print("Zenodo ERA5 Downloader - 测试")
    print("=" * 60)

    # 创建下载器
    downloader = ZenodoERA5Downloader()

    # 测试下载单个文件
    print("\n测试：下载2024-01数据")
    try:
        path = downloader.download_file('2024-01')
        print(f"\n✅ 成功下载到: {path}")
        print(f"   文件大小: {path.stat().st_size / 1024 / 1024:.1f} MB")
    except Exception as e:
        print(f"\n❌ 下载失败: {str(e)}")
        print("\n⚠️ 注意：需要先上传ERA5数据到Zenodo并更新ZENODO_RECORD_ID")

    # 显示缓存信息
    print("\n缓存信息:")
    cache_info = downloader.get_cache_info()
    print(f"  文件数量: {cache_info['num_files']}")
    print(f"  总大小: {cache_info['total_size_mb']:.1f} MB")
    if cache_info['files']:
        print(f"  文件列表: {', '.join(cache_info['files'])}")
