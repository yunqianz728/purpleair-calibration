# Zenodo ERA5数据上传和配置指南

**目标**：将47GB ERA5数据上传到Zenodo，实现Web应用自动下载

---

## 📋 步骤概览

1. ✅ 准备ERA5数据文件
2. ✅ 上传到Zenodo
3. ✅ 获取Record ID
4. ✅ 配置Web应用
5. ✅ 测试自动下载
6. ✅ 部署到Streamlit Cloud

---

## 第1步：准备ERA5数据文件

### **当前数据位置**
```
/Users/yunqianzhang/Desktop/PA/气象数据/
```

### **检查文件列表**

运行以下命令查看所有文件：

```bash
cd /Users/yunqianzhang/Desktop/PA/气象数据/
ls -lh *.nc

# 应该看到类似：
# 2022-01.nc  (1.5 GB)
# 2022-02.nc  (1.5 GB)
# ...
# 2024-12.nc  (1.5 GB)
```

### **验证文件总大小**

```bash
du -sh /Users/yunqianzhang/Desktop/PA/气象数据/
# 应该显示约47GB
```

### **文件命名格式**
确保所有文件格式为：`YYYY-MM.nc`（例如：`2024-01.nc`）

如果格式不对，需要重命名。

---

## 第2步：上传到Zenodo

### **A. 登录Zenodo**

1. 访问：https://zenodo.org/
2. 使用你的账号登录（或注册新账号）
   - 推荐使用GitHub账号登录（更方便）

### **B. 创建新Upload**

1. 点击右上角 "Upload" → "New upload"
2. 进入上传页面

### **C. 上传文件**

#### **方法1：网页上传（推荐，小于10GB）**

```
1. 点击 "Choose files"
2. 选择所有.nc文件（可以一次选多个）
3. 等待上传完成

⚠️ 限制：网页上传单次最大10GB，需要分批上传
```

#### **方法2：命令行上传（推荐，适合大文件）**

**安装Zenodo CLI工具**：
```bash
pip install zenodo-client
```

**上传所有文件**：
```bash
# 1. 创建upload（获取deposition ID）
zenodo_client deposit create

# 2. 上传所有NC文件
cd /Users/yunqianzhang/Desktop/PA/气象数据/
for file in *.nc; do
    zenodo_client file add --deposition <DEPOSITION_ID> "$file"
done

# 3. 发布
zenodo_client deposit publish --deposition <DEPOSITION_ID>
```

### **D. 填写元数据**

在上传页面填写：

```
Title:
    ERA5 Reanalysis Data for PurpleAir Temperature Calibration (2022-2024)

Authors:
    - Yunqian Zhang
    - Lu Liang

Description:
    Hourly ERA5 meteorological reanalysis data for the continental United States
    (CONUS) from January 2022 to December 2024. This dataset supports the
    PurpleAir temperature sensor calibration project.

    Variables included:
    - sshf: Surface sensible heat flux
    - ssrd: Surface solar radiation downwards
    - strd: Surface thermal radiation downwards
    - tp: Total precipitation
    - u10: 10m U wind component
    - v10: 10m V wind component

    Spatial coverage: CONUS (24°N-50°N, -125°W to -65°W)
    Temporal resolution: Hourly
    Spatial resolution: 0.25° × 0.25°

    Related publication: "Nationwide Calibration of PurpleAir Temperature
    Sensors for Heat Exposure Research"

    Data source: ERA5 (Copernicus Climate Data Store)
    https://cds.climate.copernicus.eu/

License:
    CC BY 4.0 (Creative Commons Attribution)

Keywords:
    - ERA5
    - meteorological data
    - PurpleAir
    - temperature calibration
    - reanalysis
    - CONUS

Related Identifiers:
    - Is supplemented by: 10.5281/zenodo.18463819 (代码仓库)
    - Is cited by: [你的论文DOI，如果已发表]

Upload type:
    Dataset

Access right:
    Open Access
```

### **E. 发布**

1. 检查所有信息
2. 点击 "Publish"
3. **重要**：发布后会获得一个**永久DOI**和**Record ID**

**示例**：
```
DOI: 10.5281/zenodo.1234567
Record ID: 1234567  ← 这个很重要！
```

---

## 第3步：获取下载链接

发布后，每个文件都有一个直接下载链接：

**格式**：
```
https://zenodo.org/record/<RECORD_ID>/files/<FILENAME>
```

**示例**：
```
https://zenodo.org/record/1234567/files/2024-01.nc
https://zenodo.org/record/1234567/files/2024-02.nc
...
```

**测试下载**：
```bash
# 测试单个文件是否可下载
curl -O "https://zenodo.org/record/1234567/files/2024-01.nc"
```

---

## 第4步：配置Web应用

### **A. 更新Zenodo Record ID**

编辑 `app/utils/zenodo_downloader.py`：

```python
# 第13行，替换为你的Record ID
ZENODO_RECORD_ID = "1234567"  # ← 改成你的实际ID
```

### **B. 配置环境变量（Streamlit Cloud部署）**

在 `.streamlit/secrets.toml` 中添加：

```toml
# Zenodo配置
ZENODO_RECORD_ID = "1234567"
USE_ZENODO = "true"
```

### **C. 更新requirements.txt**

确保包含：
```
tqdm>=4.65.0  # 用于下载进度条
requests>=2.28.0  # 用于HTTP下载
```

---

## 第5步：本地测试

### **测试自动下载**

```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration/app

# 测试下载器
python utils/zenodo_downloader.py
```

**预期输出**：
```
Zenodo ERA5 Downloader - 测试
============================================================

测试：下载2024-01数据
📥 Downloading 2024-01.nc from Zenodo...
   URL: https://zenodo.org/record/1234567/files/2024-01.nc
2024-01.nc: 100%|████████| 1.5GB/1.5GB [01:23<00:00, 18.0MB/s]

✅ 成功下载到: /tmp/era5_cache/2024-01.nc
   文件大小: 1524.3 MB

缓存信息:
  文件数量: 1
  总大小: 1524.3 MB
  文件列表: 2024-01.nc
```

### **测试完整校准流程**

```bash
# 使用Zenodo模式运行测试
export USE_ZENODO=true
export ZENODO_RECORD_ID=1234567

python test_calibration.py
```

**预期**：自动从Zenodo下载需要的月份数据，然后完成校准

---

## 第6步：部署到Streamlit Cloud

### **A. 更新代码到GitHub**

```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration

# 添加新文件
git add app/utils/zenodo_downloader.py
git add ZENODO_SETUP_GUIDE.md
git add app/utils/era5_reader.py  # 已修改

# 提交
git commit -m "Add Zenodo auto-download support for ERA5 data

✅ Implement ZenodoERA5Downloader
✅ Update ERA5Reader to support Zenodo
✅ Enable automatic file download from Zenodo
✅ Add comprehensive setup guide

Users can now deploy to cloud platforms without local ERA5 files"

# 推送
git push origin main
```

### **B. 在Streamlit Cloud配置**

1. 访问：https://share.streamlit.io/
2. 选择你的仓库：`yunqianz728/purpleair-calibration`
3. 主文件路径：`app/app.py`
4. **添加Secrets**（重要！）：

   点击 "Advanced settings" → "Secrets"

   添加：
   ```toml
   ZENODO_RECORD_ID = "1234567"
   USE_ZENODO = "true"
   ```

5. 点击 "Deploy"

### **C. 首次启动**

⚠️ **注意**：
- 首次启动会较慢（需要下载ERA5数据）
- 如果超过15分钟会超时 → 需要用户多次刷新页面
- 后续使用会更快（有缓存）

**优化方案**：
- 在App启动时预下载常用月份（如最近3个月）
- 显示友好的加载提示

---

## 第7步：更新文档

### **更新README.md**

添加Zenodo数据集链接：

```markdown
## 📊 Data Availability

- **Code**: https://github.com/yunqianz728/purpleair-calibration
- **ERA5 Data**: https://zenodo.org/record/1234567 (47 GB)
- **Models**: Included in repository (44 MB)

The web application automatically downloads ERA5 data from Zenodo as needed.
```

### **更新论文main.tex**

在 "Open Data and User Interface" 部分添加：

```latex
ERA5 meteorological data (2022-2024) used for calibration is archived
at Zenodo \citep{zenodo_era5_dataset} (DOI: 10.5281/zenodo.1234567),
enabling full reproducibility without requiring users to download
large datasets locally.
```

添加引用到`references.bib`：

```bibtex
@dataset{zenodo_era5_dataset,
  author       = {Zhang, Yunqian and Liang, Lu},
  title        = {ERA5 Reanalysis Data for PurpleAir Temperature
                  Calibration (2022-2024)},
  month        = feb,
  year         = 2026,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.1234567},
  url          = {https://doi.org/10.5281/zenodo.1234567}
}
```

---

## 🎯 完成后的用户体验

### **本地运行**（有ERA5本地文件）
```
启动速度：<5秒
数据来源：本地文件
用户体验：⭐⭐⭐⭐⭐
```

### **云端部署**（Streamlit Cloud + Zenodo）
```
首次启动：2-5分钟（下载需要的月份）
后续使用：<30秒（缓存）
数据来源：Zenodo自动下载
用户体验：⭐⭐⭐⭐
```

### **用户操作流程**
```
1. 访问网站 URL
2. 上传CSV文件
3. 等待（第一次较慢，显示"正在从Zenodo下载数据..."）
4. 获得校准结果
5. 下载结果CSV
```

**完全自动**，用户无需了解Zenodo或ERA5！

---

## ⚠️ 注意事项

### **Zenodo限制**
- ✅ 免费，无限制
- ✅ 50 GB/数据集（你的47GB OK）
- ✅ 永久保存
- ⚠️ 发布后无法修改（只能创建新版本）

### **Streamlit Cloud限制**
- ⚠️ 临时存储：重启后清空缓存
- ⚠️ 启动超时：15分钟（首次下载可能超时）
- ⚠️ 内存限制：1 GB

### **优化建议**
1. **预下载热门月份**：在App启动时预下载最近3个月
2. **智能缓存管理**：自动删除旧文件，保持最多5GB缓存
3. **进度显示**：显示下载进度给用户
4. **错误处理**：友好的错误提示

---

## 📞 需要帮助？

遇到问题？检查：
1. ✅ Zenodo Record ID是否正确
2. ✅ 文件命名是否为`YYYY-MM.nc`格式
3. ✅ Zenodo数据集是否为"Open Access"
4. ✅ 环境变量`USE_ZENODO=true`是否设置

---

**准备好了吗？要开始上传ERA5数据到Zenodo吗？** 🚀
