# 🚀 Streamlit Cloud 部署步骤 - 3分钟完成

## 第1步：打开Streamlit Cloud (30秒)

1. 在浏览器打开新标签页
2. 访问: **https://streamlit.io/cloud**
3. 点击右上角 **"Sign up"** 或 **"Sign in"**
4. 选择 **"Continue with GitHub"**
5. 授权Streamlit访问您的GitHub

---

## 第2步：创建新应用 (1分钟)

### 点击 "New app" 按钮

在Streamlit Cloud控制台，点击蓝色的 **"New app"** 按钮

### 填写三个关键信息

在弹出的表单中填写:

#### 1. Repository (仓库)
```
yunqianz728/purpleair-calibration
```
*注意: 精确输入，或从下拉菜单选择*

#### 2. Branch (分支)
```
main
```

#### 3. Main file path (主文件路径)
```
app/app.py
```
*注意: 必须包含 `app/` 前缀*

### (可选) 自定义URL

在 "App URL" 字段可以自定义:
- 默认: `yunqianz728-purpleair-calibration.streamlit.app`
- 自定义: `purpleair-temp-calibration.streamlit.app`

---

## 第3步：部署！(2分钟)

### 点击 "Deploy!" 按钮

点击右下角的蓝色 **"Deploy!"** 按钮

### 等待构建完成

您会看到部署日志:

```
⏳ Cloning repository...
⏳ Installing dependencies from app/requirements.txt...
⏳ Installing streamlit...
⏳ Installing pandas...
⏳ Installing numpy...
⏳ Installing plotly...
✅ App is live!
```

通常需要 **1-2分钟**

### 部署成功！

当看到 **绿色勾号 ✅** 和 **"Your app is live!"** 时，部署完成！

---

## 🎉 完成！访问您的应用

您的应用现在在线了:

```
https://yunqianz728-purpleair-calibration.streamlit.app
```

*(或您自定义的URL)*

---

## 📱 测试应用

1. **打开应用** - 点击上面的链接
2. **上传文件** - 拖拽一个CSV测试
3. **查看结果** - 验证校准功能正常
4. **分享链接** - 复制URL发给同事

---

## 🔄 自动更新

从现在开始，每次您推送代码到GitHub:

```bash
git push origin main
```

Streamlit会**自动重新部署**（约2分钟）

无需手动操作！

---

## 🛠️ 管理应用

### 查看应用状态

1. 访问 Streamlit Cloud 控制台
2. 点击您的应用
3. 查看:
   - 访问量统计
   - 错误日志
   - 性能指标

### 重启应用

如果应用出错:
1. 点击应用右上角 "⚙️"
2. 选择 "Reboot app"

### 暂停/删除应用

1. 应用设置 → "Settings"
2. 选择 "Sleep" (暂停) 或 "Delete" (删除)

---

## 📧 需要帮助？

### 遇到问题？

**常见问题**:

1. **"Repository not found"**
   - 检查拼写: `yunqianz728/purpleair-calibration`
   - 确保仓库是public
   - 重新授权GitHub

2. **"requirements.txt not found"**
   - 确认文件路径: `app/app.py` (不是 `app.py`)
   - 检查GitHub仓库中文件是否存在

3. **"App failed to build"**
   - 查看完整日志
   - 可能是依赖版本问题
   - 尝试重新部署

**获取支持**:
- Streamlit论坛: https://discuss.streamlit.io/
- 项目Issues: https://github.com/yunqianz728/purpleair-calibration/issues

---

## ✅ 检查清单

部署后确认:

- [ ] 应用成功部署（绿色勾号）
- [ ] 可以访问URL
- [ ] 页面正常加载
- [ ] 可以上传CSV
- [ ] 校准功能正常
- [ ] 可以下载结果

全部打勾？**恭喜您，部署成功！** 🎉

---

## 📝 下一步

### 更新论文

在论文中添加应用链接:

```latex
\section*{Open Data and User Interface}

A user-friendly web interface is freely available at
\url{https://yunqianz728-purpleair-calibration.streamlit.app}
for calibrating PurpleAir temperature data without programming.
```

### 更新README

在GitHub README添加徽章:

```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://yunqianz728-purpleair-calibration.streamlit.app)
```

### 分享链接

- Email: 发给合作者
- Twitter: 分享给研究社区
- ResearchGate: 添加到项目

---

**总耗时: 3分钟** ⏱️
**难度: ⭐ 非常简单**
**费用: 💰 完全免费**

立即开始部署吧！🚀
