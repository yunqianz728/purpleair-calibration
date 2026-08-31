# 如何获取Zenodo DOI号 - 快速指南

## 🎯 DOI生成的完整时间线

```
步骤1: 创建GitHub Release
    ↓ (立即)
步骤2: Zenodo连接仓库（开关打开）
    ↓ (5-10分钟)
Zenodo自动检测到新Release
    ↓ (自动处理)
Zenodo创建存档并生成DOI
    ↓ (完成！)
您可以获取DOI号
```

**总耗时**: 通常5-10分钟，最长可能30分钟

---

## ✅ 检查DOI是否已生成

### 快速检查清单

- [ ] 您已创建GitHub Release (v1.0.0)
- [ ] 您已在Zenodo登录并连接仓库
- [ ] 等待至少10分钟
- [ ] 收到Zenodo的邮件通知

---

## 🔍 四种获取DOI的方法

### 方法1: Zenodo GitHub页面（推荐⭐）

**访问**: https://zenodo.org/account/settings/github/

**步骤**:
1. 用GitHub账号登录Zenodo
2. 找到 `purpleair-calibration` 仓库
3. 查看DOI信息：

```
✅ purpleair-calibration [ON]

Latest upload:
📦 DOI: 10.5281/zenodo.1234567
🔗 https://doi.org/10.5281/zenodo.1234567
```

**如果看到DOI号** → 复制保存！
**如果看不到DOI** → 检查下面的故障排除

---

### 方法2: 邮件通知

**检查您的邮箱** (GitHub注册邮箱)

**邮件主题**:
```
Zenodo: GitHub release published
```

**邮件内容示例**:
```
Your GitHub repository release has been published on Zenodo.

Repository: yunqianz728/purpleair-calibration
Release: v1.0.0
DOI: 10.5281/zenodo.1234567

View on Zenodo: https://zenodo.org/record/1234567
```

---

### 方法3: Zenodo搜索

**访问**: https://zenodo.org/

**步骤**:
1. 在搜索框输入:
   ```
   purpleair-calibration yunqianz728
   ```

2. 找到您的记录（标题: "yunqianz728/purpleair-calibration: v1.0.0"）

3. DOI显示在标题下方:
   ```
   DOI: 10.5281/zenodo.1234567
   ```

---

### 方法4: 直接访问您的Zenodo上传

**访问**: https://zenodo.org/me/uploads

**步骤**:
1. 登录Zenodo
2. 查看 "Uploads" 列表
3. 找到 `purpleair-calibration v1.0.0`
4. 点击查看详情，DOI显示在页面顶部

---

## 🆘 故障排除：如果看不到DOI

### 问题1: Zenodo页面上仓库旁边没有DOI

**可能原因**:
- ✗ Zenodo连接设置不正确
- ✗ Release是在连接Zenodo之前创建的
- ✗ Release标记为 "Draft"（草稿）

**解决方案**:

#### 方案A: 检查连接状态
1. 访问: https://zenodo.org/account/settings/github/
2. 确认 `purpleair-calibration` 旁边的开关是**绿色ON**
3. 如果是灰色OFF，点击打开

#### 方案B: 创建新Release触发同步
```bash
# 如果v1.0.0没有触发，创建v1.0.1
```
1. 访问: https://github.com/yunqianz728/purpleair-calibration/releases
2. 创建新Release: v1.0.1
3. 等待10分钟让Zenodo处理

#### 方案C: 手动触发同步
1. 在Zenodo GitHub页面
2. 找到 `purpleair-calibration`
3. 点击 "Sync now" 按钮（如果有）

---

### 问题2: 等待超过30分钟还没有DOI

**解决方案**:

1. **检查GitHub Release状态**
   - 访问: https://github.com/yunqianz728/purpleair-calibration/releases
   - 确认Release已发布（不是Draft）

2. **检查Zenodo服务状态**
   - 访问: https://status.zenodo.org/
   - 查看是否有服务中断

3. **联系Zenodo支持**
   - 邮箱: info@zenodo.org
   - 说明: "GitHub release not creating DOI"
   - 提供仓库链接

---

### 问题3: 收到错误邮件

**可能的错误**:
```
Zenodo was unable to create a DOI for your release
```

**解决方案**:
1. 检查Release中是否包含无效文件（超大文件、特殊字符等）
2. 确认仓库是Public（Zenodo不支持Private仓库）
3. 重新创建Release

---

## 📋 DOI格式说明

### 标准格式
```
10.5281/zenodo.1234567
```

**组成部分**:
- `10.5281` - Zenodo的DOI前缀（固定）
- `zenodo` - Zenodo平台标识（固定）
- `1234567` - 您的记录唯一编号（**7位数字，会变化**）

### 完整URL
```
https://doi.org/10.5281/zenodo.1234567
```

### 版本DOI vs 概念DOI

Zenodo为每个项目生成**两个DOI**：

#### 概念DOI（Concept DOI）- 推荐用于论文
```
10.5281/zenodo.1234567
```
- 始终指向最新版本
- 用于引用整个项目

#### 版本DOI（Version DOI）- 用于精确引用
```
10.5281/zenodo.1234568
```
- 指向特定版本（v1.0.0）
- 用于精确复现

**建议**: 论文中使用**概念DOI**（较短的那个），这样即使您更新代码，DOI仍然有效。

---

## 📝 获取DOI后的操作

### 1. 记录DOI号
将DOI号保存到文本文件:
```
10.5281/zenodo.1234567
```

### 2. 更新README.md
```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1234567.svg)](https://doi.org/10.5281/zenodo.1234567)
```

### 3. 更新CITATION.cff
```yaml
doi: 10.5281/zenodo.1234567
```

### 4. 更新论文main.tex
```latex
(archived version: \url{https://doi.org/10.5281/zenodo.1234567})
```

### 5. 提交更改
```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration
git add README.md CITATION.cff
git commit -m "Add Zenodo DOI"
git push origin main
```

---

## 🎯 快速验证DOI

获取DOI后，验证其有效性：

### 方法1: 浏览器访问
```
https://doi.org/10.5281/zenodo.1234567
```
应该跳转到您的Zenodo记录页面

### 方法2: 命令行验证
```bash
curl -I https://doi.org/10.5281/zenodo.1234567
```
应该返回 `HTTP/2 302` (重定向成功)

### 方法3: DOI解析服务
访问: https://dx.doi.org/10.5281/zenodo.1234567

---

## 📧 需要帮助？

### Zenodo支持
- **帮助文档**: https://help.zenodo.org/
- **联系邮箱**: info@zenodo.org
- **GitHub集成FAQ**: https://help.zenodo.org/docs/profile/linking-accounts/#github

### 常见问题
- **Q**: DOI多久会生成？
  **A**: 通常5-10分钟，最长30分钟

- **Q**: 我可以自定义DOI号吗？
  **A**: 不可以，Zenodo自动分配

- **Q**: DOI会过期吗？
  **A**: 不会，DOI是永久的

- **Q**: 我可以删除DOI吗？
  **A**: 不可以，但可以标记为"已撤回"

---

## ✅ 成功标志

当您成功获取DOI后，应该看到：

1. ✅ Zenodo GitHub页面显示DOI号
2. ✅ 收到Zenodo的确认邮件
3. ✅ 可以访问 `https://doi.org/10.5281/zenodo.XXXXXXX`
4. ✅ Zenodo记录页面显示您的仓库信息
5. ✅ 可以下载引用格式（BibTeX, APA, etc.）

---

**最后更新**: 2026-02-02
**适用于**: GitHub + Zenodo集成
**预计完成时间**: 15分钟（包括等待）
