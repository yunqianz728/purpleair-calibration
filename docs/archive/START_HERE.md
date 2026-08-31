# 🚀 开始部署 - 只需3个操作

**我已经完成**：✅ 所有代码、✅ 所有测试、✅ 所有脚本

**你需要做**：👆 只需要这3个操作（复制粘贴命令）

---

## 📍 你现在的位置

```
✅ 代码已完成
✅ 测试已通过
✅ ERA5数据已准备好（31个文件，46.52 GB）
✅ 上传脚本已就绪
📍 你在这里 → 需要获取Zenodo token
```

---

## 操作1️⃣：获取Zenodo Token（2分钟）

### **复制这个链接，粘贴到浏览器：**
```
https://zenodo.org/account/settings/applications/tokens/new/
```

### **在打开的页面：**
1. Name填写：`PurpleAir Upload`
2. Scopes勾选：`deposit:write` ✓
3. 点击：`Create`
4. **复制显示的token**（很长的字符串）

```
示例：
eyJhbGciOiJIUzUxMiIsImlhdCI6M...（很长）...xyz123
```

### **保存token到文件：**
```bash
# 复制粘贴运行（把YOUR_TOKEN替换成刚才复制的token）
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration
echo "export ZENODO_ACCESS_TOKEN='YOUR_TOKEN'" > .zenodo_token
source .zenodo_token
```

---

## 操作2️⃣：运行上传（1条命令，等2-3小时）

### **复制粘贴运行：**
```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration
python3 upload_to_zenodo.py
```

### **会问你：**
```
Proceed with upload? (yes/no):
```
**输入**：`yes` 然后回车

### **然后等待：**
```
📤 Uploading: 2022-06.nc
2022-06.nc: 100%|████████| 1.6GB/1.6GB [02:15<00:00, 11.8MB/s]
✅ Uploaded: 2022-06.nc

📤 Uploading: 2022-07.nc
...（继续上传31个文件）
```

⏰ **总时间**：约2-3小时（可以去做别的事）

### **完成后会显示：**
```
🎉 SUCCESS! Dataset published to Zenodo
======================================================================

✅ DOI: 10.5281/zenodo.1234567
✅ Record ID: 1234567
✅ Saved to: ZENODO_RECORD_ID.txt
```

**🎯 记下Record ID！下一步需要**

---

## 操作3️⃣：部署到Streamlit Cloud（5分钟点击）

### **3.1 更新代码（复制粘贴运行）：**
```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration

# 自动读取Record ID并更新
RECORD_ID=$(cat ZENODO_RECORD_ID.txt)
sed -i '' "s/XXXXXXX/$RECORD_ID/" app/utils/zenodo_downloader.py
sed -i '' "s/XXXXXXX/$RECORD_ID/" .streamlit/secrets.toml

# 提交到GitHub
git add -A
git commit -m "Add Zenodo Record ID: $RECORD_ID"
git push origin main
```

### **3.2 部署（网页点击）：**

**访问这个链接：**
```
https://share.streamlit.io/deploy
```

**填写：**
```
Repository: yunqianz728/purpleair-calibration
Branch: main
Main file path: app/app.py
```

**点击 Advanced settings：**

**在Secrets框中粘贴：**
```toml
ZENODO_RECORD_ID = "1234567"
USE_ZENODO = "true"
```
（把1234567改成你的实际Record ID）

**点击：Deploy**

⏰ 等待5分钟

### **完成！你的网站：**
```
https://purpleair-calibration-[随机字符].streamlit.app
```

---

## 🎯 总结

| 操作 | 时间 | 你需要做 |
|------|------|----------|
| 1️⃣ 获取token | 2分钟 | 浏览器操作 + 复制粘贴1条命令 |
| 2️⃣ 运行上传 | 2-3小时 | 复制粘贴1条命令 + 输入yes |
| 3️⃣ 部署云端 | 5分钟 | 复制粘贴1条命令 + 网页点击 |
| **总计** | **~3小时** | **实际操作：10分钟** |

---

## ✅ 检查清单

- [ ] 操作1：获取Zenodo token（2分钟）
- [ ] 操作2：运行上传脚本（1条命令 + 等待）
- [ ] 操作3：部署到Streamlit Cloud（1条命令 + 点击）
- [ ] 🎉 完成！

---

## 🆘 遇到问题？

### **Token获取失败**
- 确保已登录Zenodo
- 确保勾选了`deposit:write`

### **上传中断**
```bash
# 重新运行即可，会继续上传
python3 upload_to_zenodo.py
```

### **Record ID找不到**
```bash
# 查看文件
cat ZENODO_RECORD_ID.txt
```

---

## 🚀 现在开始！

**第一条命令（获取token后）：**
```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration
echo "export ZENODO_ACCESS_TOKEN='粘贴你的token'" > .zenodo_token
source .zenodo_token
python3 upload_to_zenodo.py
```

**去获取token：**
https://zenodo.org/account/settings/applications/tokens/new/

---

**准备好了？ 🎯**
