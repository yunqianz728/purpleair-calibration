# 🚀 一键部署指南 - 完全自动化

**目标**：3个简单步骤，完成从本地到在线的完整部署

---

## ✅ 准备工作已完成

我已经帮你完成：
- ✅ 所有代码实现（Zenodo自动下载）
- ✅ 自动上传脚本
- ✅ 配置文件模板
- ✅ 部署文档

**你的ERA5数据**：
- 📁 位置：`/Users/yunqianzhang/Desktop/PA/气象数据/`
- 📊 文件数：31个（2022-06 到 2024-12）
- 💾 总大小：47 GB
- ✅ 格式正确：YYYY-MM.nc

---

## 🎯 你只需要做3件事

### **第1步：获取Zenodo Access Token** ⏰ 2分钟

1. 访问：https://zenodo.org/account/settings/applications/tokens/new/
2. 填写：
   - Name: `PurpleAir ERA5 Upload`
   - Scopes: 勾选 `deposit:write`
3. 点击 "Create"
4. **复制token**（只显示一次！）

```
示例token：
eyJhbGc...很长的字符串...xyz123
```

**暂时保存**在某处（稍后需要）

---

### **第2步：运行一键上传脚本** ⏰ 2-3小时（自动运行）

```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration

# 运行上传脚本
python3 upload_to_zenodo.py
```

**脚本会自动**：
1. ✅ 检查31个文件
2. ✅ 询问你确认
3. ✅ 要求粘贴token（粘贴第1步的token）
4. ✅ 创建Zenodo deposition
5. ✅ 上传所有文件（显示进度条）
6. ✅ 添加完整元数据
7. ✅ 发布并获得DOI
8. ✅ 保存Record ID到文件

**你需要做的**：
- 粘贴token
- 等待上传完成（可以去做别的事）

**完成后会显示**：
```
🎉 SUCCESS! Dataset published to Zenodo
======================================================================

✅ DOI: 10.5281/zenodo.1234567
✅ Record ID: 1234567
✅ URL: https://zenodo.org/record/1234567

📝 Next steps:
1. Update app/utils/zenodo_downloader.py:
   ZENODO_RECORD_ID = "1234567"
```

---

### **第3步：部署到Streamlit Cloud** ⏰ 5分钟

#### **3.1 更新代码**

脚本会生成 `ZENODO_RECORD_ID.txt`，运行：

```bash
# 自动更新Record ID
RECORD_ID=$(cat ZENODO_RECORD_ID.txt)
sed -i '' "s/ZENODO_RECORD_ID = \"XXXXXXX\"/ZENODO_RECORD_ID = \"$RECORD_ID\"/" app/utils/zenodo_downloader.py

# 提交到GitHub
git add -A
git commit -m "Update Zenodo Record ID: $RECORD_ID"
git push origin main
```

#### **3.2 部署到Streamlit Cloud**

1. **访问**：https://share.streamlit.io/

2. **登录**（用GitHub账号）

3. **点击** "New app"

4. **填写**：
   ```
   Repository: yunqianz728/purpleair-calibration
   Branch: main
   Main file path: app/app.py
   ```

5. **点击** "Advanced settings"

6. **添加Secrets**（粘贴以下内容）：
   ```toml
   ZENODO_RECORD_ID = "1234567"  # 替换为实际ID
   USE_ZENODO = "true"
   ```

7. **点击** "Deploy"

8. **等待3-5分钟**，完成！

**你的在线网站**：
```
https://purpleair-calibration-[random].streamlit.app
```

---

## 📋 完整时间表

| 步骤 | 时间 | 你的操作 | 自动化 |
|------|------|----------|--------|
| 1. 获取token | 2分钟 | ✋ 手动 | - |
| 2. 运行上传 | 2-3小时 | ✋ 启动 | ✅ 自动 |
| 3. 更新代码 | 1分钟 | ✋ 复制粘贴 | ✅ 命令 |
| 4. 部署云端 | 5分钟 | ✋ 点击 | ✅ 自动 |
| **总计** | **~3小时** | **~10分钟手动** | **~2.9小时自动** |

---

## 🎉 完成后你将拥有

### **1. Zenodo数据集** ✨
```
✅ DOI: 10.5281/zenodo.[你的ID]
✅ 47GB ERA5数据
✅ 永久免费
✅ 学术引用
✅ 自动下载
```

### **2. 在线Web应用** 🌐
```
✅ URL: https://[你的app].streamlit.app
✅ 完全功能
✅ 自动从Zenodo获取数据
✅ 用户友好
✅ 免费托管
```

### **3. GitHub仓库** 💻
```
✅ 完整代码
✅ 真实模型
✅ 详细文档
✅ 可复现
```

### **4. 学术论文更新** 📄
```
✅ 代码DOI: 10.5281/zenodo.18463819
✅ 数据DOI: 10.5281/zenodo.[新ID]
✅ 在线工具: https://[你的app].streamlit.app
✅ 完整可复现性
```

---

## ⚡ 立即开始

**复制粘贴运行**：

```bash
# 1. 获取token（浏览器操作，见上文）

# 2. 运行上传
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration
python3 upload_to_zenodo.py

# 3. 等待完成后，运行：
RECORD_ID=$(cat ZENODO_RECORD_ID.txt)
sed -i '' "s/XXXXXXX/$RECORD_ID/" app/utils/zenodo_downloader.py
git add -A
git commit -m "Deploy: Add Zenodo Record ID $RECORD_ID"
git push origin main

# 4. 访问 https://share.streamlit.io/ 部署
```

---

## 🆘 遇到问题？

### **上传失败**
```bash
# 重新运行即可，会继续上传
python3 upload_to_zenodo.py
```

### **Token过期**
```bash
# 重新获取token，设置环境变量
export ZENODO_ACCESS_TOKEN='your-new-token'
python3 upload_to_zenodo.py
```

### **部署超时**
```
Streamlit Cloud首次启动可能超时
解决：多刷新几次页面即可
```

---

## ✅ 检查清单

- [ ] 获取Zenodo token
- [ ] 运行 `upload_to_zenodo.py`
- [ ] 等待上传完成（2-3小时）
- [ ] 更新代码中的Record ID
- [ ] 提交推送到GitHub
- [ ] 部署到Streamlit Cloud
- [ ] 测试在线网站
- [ ] 更新论文引用

---

**准备好了吗？马上开始第1步！** 🚀

访问：https://zenodo.org/account/settings/applications/tokens/new/
