# GitHub仓库设置指南

## 🎯 目标

将这个完整的PurpleAir校准仓库上传到GitHub，供论文引用和公众使用。

---

## 📋 准备工作

### ✅ 已完成
- [x] 仓库结构创建完成 (30个文件)
- [x] 所有代码和文档已编写 (~5,000行)
- [x] Git仓库已初始化
- [x] 初始提交已创建

### ⏳ 需要完成

1. 在GitHub上创建新仓库
2. 配置远程仓库
3. 推送代码
4. 配置仓库设置
5. 更新论文中的链接

---

## 🚀 详细步骤

### 步骤 1: 在GitHub上创建新仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `purpleair-calibration`
   - **Description**: `Nationwide calibration of PurpleAir temperature sensors using machine learning`
   - **Visibility**:
     - ✅ **Public** (推荐，用于论文引用)
     - ⚠️ Private (如果论文尚未接受，可以先设为私有)
   - **Initialize repository**:
     - ❌ **不要**勾选 "Add a README file"
     - ❌ **不要**勾选 "Add .gitignore"
     - ❌ **不要**勾选 "Choose a license"
     (我们已经创建了这些文件)
3. 点击 "Create repository"

### 步骤 2: 配置Git用户信息（如果还没配置）

```bash
# 配置你的GitHub用户名和邮箱
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 更新之前的提交
cd "/Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration"
git commit --amend --reset-author --no-edit
```

### 步骤 3: 连接到GitHub远程仓库

```bash
cd "/Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration"

# 添加远程仓库（替换yourusername为你的GitHub用户名）
git remote add origin https://github.com/yourusername/purpleair-calibration.git

# 验证远程仓库
git remote -v
```

### 步骤 4: 推送代码到GitHub

```bash
# 推送到main分支
git push -u origin main
```

如果推送失败（可能需要认证），有两个选项：

#### 选项 A: 使用Personal Access Token（推荐）

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置：
   - Note: `purpleair-calibration`
   - Expiration: `90 days` 或更长
   - Scopes: 勾选 `repo` (所有子选项)
4. 点击 "Generate token"
5. **立即复制token**（只显示一次！）
6. 推送时使用token作为密码：

```bash
git push -u origin main
# Username: your-github-username
# Password: <粘贴你的token>
```

#### 选项 B: 使用SSH Key

```bash
# 生成SSH key（如果还没有）
ssh-keygen -t ed25519 -C "your.email@example.com"

# 添加SSH key到GitHub
# 1. 复制公钥
cat ~/.ssh/id_ed25519.pub
# 2. 访问 https://github.com/settings/keys
# 3. 点击 "New SSH key"
# 4. 粘贴公钥内容

# 更改远程URL为SSH格式
git remote set-url origin git@github.com:yourusername/purpleair-calibration.git

# 推送
git push -u origin main
```

---

## ⚙️ GitHub仓库配置（推送后）

### 1. 配置仓库主题和描述

在仓库页面：
1. 点击右上角的 "⚙️ Settings"
2. 在 "General" → "Social preview" 部分：
   - 上传一个项目预览图（可选，推荐尺寸 1280x640）
3. 在顶部添加 Topics:
   ```
   machine-learning
   sensor-calibration
   purpleair
   temperature
   climate
   environmental-science
   xgboost
   python
   heat-exposure
   urban-climate
   ```

### 2. 启用 GitHub Pages（可选，用于文档）

1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, /docs
4. Save

你的文档将发布在: `https://yourusername.github.io/purpleair-calibration/`

### 3. 保护main分支（推荐）

1. Settings → Branches
2. Add branch protection rule
3. Branch name pattern: `main`
4. 勾选：
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging

### 4. 配置Issue模板（可选）

创建 `.github/ISSUE_TEMPLATE/bug_report.md` 和 `feature_request.md`

---

## 📊 添加仓库徽章

在推送后，GitHub会自动生成一些信息。更新README.md中的徽章：

```bash
cd "/Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration"

# 编辑README.md，更新以下行：
# 第4行: 将 yourusername 替换为你的GitHub用户名
# 第5行: 论文被接受后，更新DOI
# 第6行: 如果有Hugging Face演示，更新链接
```

---

## 🎓 更新论文中的引用

### 在主文档 (main.tex) 中

#### 1. Code Availability 部分

```latex
\section*{Code Availability}

The complete code for data preprocessing, model training, and evaluation
is publicly available at:

\textbf{GitHub Repository:}
\url{https://github.com/yourusername/purpleair-calibration}

\textbf{Archived Version:}
Zenodo DOI: 10.5281/zenodo.XXXXXXX (version v1.0.0)

\textbf{Web Interface:}
\url{https://huggingface.co/spaces/yunqianz/purpleair-calibration}
```

#### 2. SI文档中添加

```latex
\subsection*{Code and Data Availability}

All code is available at \url{https://github.com/yourusername/purpleair-calibration}
under the MIT License with citation requirement.

Installation:
\begin{verbatim}
git clone https://github.com/yourusername/purpleair-calibration.git
cd purpleair-calibration
conda env create -f environment.yml
conda activate purpleair-calib
\end{verbatim}
```

---

## 📦 创建Zenodo存档（用于DOI）

### 为什么需要Zenodo？

GitHub仓库可能会改变，但Zenodo提供永久DOI，适合学术引用。

### 步骤：

1. **连接GitHub到Zenodo**
   - 访问 https://zenodo.org/account/settings/github/
   - 用GitHub账号登录
   - 授权Zenodo访问你的仓库

2. **启用仓库存档**
   - 在Zenodo的GitHub页面找到 `purpleair-calibration`
   - 切换开关启用

3. **创建Release触发存档**
   ```bash
   # 在GitHub上创建release
   # 或使用命令行：
   git tag -a v1.0.0 -m "Initial release for paper publication"
   git push origin v1.0.0
   ```

4. **在GitHub上创建Release**
   - 访问 `https://github.com/yourusername/purpleair-calibration/releases`
   - 点击 "Create a new release"
   - Tag version: `v1.0.0`
   - Release title: `v1.0.0 - Initial Publication Release`
   - Description:
     ```markdown
     Initial release accompanying the paper:

     **Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research**

     Yunqian Zhang, Yan Rong, Lu Liang

     ## Highlights
     - Complete 63-feature engineering implementation
     - Temporal-TempStrat calibration model
     - MAE: 0.38-0.53°C across temperature ranges
     - 90% error reduction vs. uncalibrated sensors

     ## Citation
     If you use this code, please cite:
     [Paper citation once published]
     ```
   - 点击 "Publish release"

5. **获取Zenodo DOI**
   - Zenodo会自动为release创建DOI
   - 访问 https://zenodo.org/account/settings/github/
   - 找到你的仓库，点击DOI徽章
   - 复制DOI (格式: 10.5281/zenodo.XXXXXXX)

6. **更新README和论文**
   - 将Zenodo DOI添加到README.md第5行
   - 更新论文中的引用

---

## ✅ 验证清单

推送完成后，检查：

- [ ] 代码已成功推送到GitHub
- [ ] README在GitHub上正确显示
- [ ] 所有文件都已上传（30个文件）
- [ ] 徽章显示正确
- [ ] LICENSE文件可见
- [ ] Topics已添加
- [ ] 仓库描述已设置
- [ ] Zenodo DOI已创建（如果适用）
- [ ] 论文中的GitHub链接已更新
- [ ] Web界面链接已更新（如果有）

---

## 🎯 最终检查

在仓库公开之前：

1. **测试安装**
   ```bash
   # 在新环境中测试
   conda create -n test-env python=3.10
   conda activate test-env
   git clone https://github.com/yourusername/purpleair-calibration.git
   cd purpleair-calibration
   pip install -e .
   python examples/quick_start_example.py
   ```

2. **检查README**
   - 所有链接都可点击
   - 示例代码可以运行
   - 安装说明清晰

3. **验证引用**
   - CITATION.cff格式正确
   - 论文信息完整

---

## 📞 后续支持

### 添加贡献者指南

已包含在 `CONTRIBUTING.md`

### 设置GitHub Discussions（可选）

1. Settings → Features
2. 启用 "Discussions"
3. 创建类别：
   - Q&A（问答）
   - Ideas（想法）
   - Show and tell（展示）

### 添加GitHub Actions（未来）

可以添加自动化测试和文档部署：
- `.github/workflows/tests.yml` - 运行单元测试
- `.github/workflows/docs.yml` - 自动部署文档

---

## 🎉 完成！

完成以上步骤后，你的仓库将：

✅ 公开可访问
✅ 有永久DOI（通过Zenodo）
✅ 可以在论文中引用
✅ 可供其他研究者使用和贡献
✅ 专业且易用

**你的研究将对科学界产生最大影响！** 🚀

---

## 📧 需要帮助？

如果遇到问题：
1. 查看GitHub文档: https://docs.github.com
2. Zenodo帮助: https://help.zenodo.org
3. 联系我们: lianglu@berkeley.edu

---

**创建日期**: 2026-02-02
**仓库路径**: `/Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration`
**状态**: 准备推送
