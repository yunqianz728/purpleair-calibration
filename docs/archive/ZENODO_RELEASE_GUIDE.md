# 创建GitHub Release和Zenodo DOI指南

## 📌 为什么需要DOI？

学术论文引用代码时，需要**永久性的引用标识符**。GitHub仓库可能会改变或删除，但**Zenodo DOI是永久的**，非常适合学术引用。

---

## 🎯 整体流程（总共15分钟）

1. **在GitHub上创建Release** (5分钟)
2. **连接Zenodo到GitHub** (5分钟)
3. **获取DOI** (自动生成)
4. **更新论文引用** (5分钟)

---

## 第一步：创建GitHub Release (5分钟)

### 1.1 访问Release页面

访问: https://github.com/yunqianz728/purpleair-calibration/releases

### 1.2 创建新Release

点击右上角的 **"Create a new release"** 按钮

### 1.3 填写Release信息

#### Tag version（必填）
```
v1.0.0
```

#### Release title（必填）
```
v1.0.0 - Initial Publication Release
```

#### Description（推荐内容）
```markdown
## 📄 Paper Reference

Initial release accompanying the paper:

**Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research**

Yunqian Zhang, Yan Rong, Lu Liang

---

## ✨ Highlights

- **63-feature engineering framework** - Complete implementation of temporal and spatial features
- **Temperature-stratified calibration** - Separate models for cold/moderate/hot thermal regimes
- **High accuracy** - MAE: 0.38-0.53°C across temperature ranges
- **90% error reduction** - Compared to uncalibrated sensors (uncalibrated MAE: 5.4°C)
- **National validation** - 2,682 sensors across 31 U.S. states, 797,744 observations
- **Production-ready** - Real-time deployment with <3ms latency

---

## 📦 What's Included

### Code
- `/models/` - Complete calibration model implementations (XGBoost, CatBoost, LightGBM)
- `/data/` - 63-feature engineering pipeline
- `/utils/` - Evaluation metrics and visualization tools
- `/examples/` - Quick start examples and tutorials

### Documentation
- `README.md` - Complete project overview and installation guide
- `docs/USAGE.md` - Step-by-step usage instructions
- `docs/FAQ.md` - Frequently asked questions (40+ Q&A)
- `CITATION.cff` - Citation metadata

### Configuration
- `environment.yml` - Conda environment specification
- `requirements.txt` - Python dependencies
- `config/model_config.yaml` - Model hyperparameters

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yunqianz728/purpleair-calibration.git
cd purpleair-calibration

# Install dependencies
conda env create -f environment.yml
conda activate purpleair-calib

# Run quick start example
python examples/quick_start_example.py
```

---

## 📊 Performance Summary

| Model | MAE (Cold) | MAE (Moderate) | MAE (Hot) | Overall RMSE |
|-------|------------|----------------|-----------|--------------|
| **Temporal-TempStrat** | **0.38°C** | **0.53°C** | **0.47°C** | **1.43°C** |
| Temporal-National | 0.77°C | 0.77°C | 0.77°C | 1.58°C |
| Spatial-Climate | 0.93°C | 0.93°C | 0.93°C | 1.71°C |
| Baseline-IDW | 2.31°C | 2.31°C | 2.31°C | 2.87°C |

---

## 📖 Citation

If you use this code in your research, please cite:

```bibtex
@article{zhang2024purpleair,
  title={Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research},
  author={Zhang, Yunqian and Rong, Yan and Liang, Lu},
  journal={[Journal Name]},
  year={2024},
  note={Code available at: https://github.com/yunqianz728/purpleair-calibration}
}
```

**DOI**: [Will be added after Zenodo archiving]

---

## 📧 Support

- **Issues**: https://github.com/yunqianz728/purpleair-calibration/issues
- **Contact**: lianglu@berkeley.edu
- **Web Interface**: https://huggingface.co/spaces/yunqianz/purpleair-calibration

---

## 📄 License

MIT License with citation requirement. See `LICENSE` for details.
```

### 1.4 发布Release

- 确认 **"Set as the latest release"** 已勾选
- 点击 **"Publish release"** 按钮

✅ **完成！** 现在您的代码有了v1.0.0版本标记

---

## 第二步：连接Zenodo到GitHub (5分钟)

### 2.1 访问Zenodo

访问: https://zenodo.org/

### 2.2 用GitHub登录

1. 点击右上角 **"Log in"**
2. 选择 **"Log in with GitHub"**
3. 授权Zenodo访问您的GitHub账号

### 2.3 连接GitHub仓库

1. 登录后，点击右上角您的用户名
2. 选择 **"GitHub"** 或访问: https://zenodo.org/account/settings/github/
3. 找到 `purpleair-calibration` 仓库
4. 将旁边的开关打开（从灰色变为绿色）✅

⚠️ **重要**: 如果您在创建Release **之前**就连接了Zenodo，Zenodo会自动为您的Release创建DOI。如果您先创建了Release，需要进行下一步。

### 2.4 创建新Release（如果需要）

如果您先创建了Release，然后才连接Zenodo，需要：

**选项A**: 创建新的Release (v1.0.1)
- GitHub会触发Zenodo创建DOI

**选项B**: 删除并重新创建v1.0.0
1. 在GitHub上删除v1.0.0 Release
2. 删除v1.0.0 tag: `git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`
3. 重新创建Release（按照第一步）

**推荐选项A**，更简单且不会破坏已有链接。

---

## 第三步：获取DOI（自动，1分钟）

### 3.1 等待Zenodo处理

- Zenodo会在几分钟内自动为您的Release创建存档
- 您会收到邮件通知

### 3.2 查看DOI

1. 访问: https://zenodo.org/account/settings/github/
2. 找到 `purpleair-calibration`
3. 点击DOI徽章或链接

DOI格式示例:
```
10.5281/zenodo.1234567
```

### 3.3 获取引用信息

在Zenodo页面，您可以找到：
- **DOI链接**: `https://doi.org/10.5281/zenodo.1234567`
- **完整引用格式**（BibTeX, APA, etc.）
- **DOI徽章**（用于README）

---

## 第四步：更新文档和论文 (5分钟)

### 4.1 更新README.md徽章

将README.md第4行的DOI徽章更新为实际DOI：

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1234567.svg)](https://doi.org/10.5281/zenodo.1234567)
```

替换 `1234567` 为您的实际Zenodo编号。

### 4.2 更新CITATION.cff

在 `CITATION.cff` 文件中添加DOI：

```yaml
doi: 10.5281/zenodo.1234567
```

### 4.3 更新论文main.tex

在 `main.tex` 的 "Open Data and User Interface" 部分添加DOI引用：

```latex
\section*{Open Data and User Interface}

To promote adoption and facilitate reproducibility, we provide open resources including:
(1) all paired PA-weather station training data, model training scripts, and evaluation
code available at \url{https://github.com/yunqianz728/purpleair-calibration} under MIT
license (archived version: \url{https://doi.org/10.5281/zenodo.1234567});
(2) a web-based calibration tool at \url{https://huggingface.co/spaces/yunqianz/purpleair-calibration}
enabling researchers, practitioners, and citizen scientists to calibrate PA temperature
readings in real time without programming requirements.
```

### 4.4 提交更新

```bash
cd /Users/yunqianzhang/Dropbox/应用/Overleaf/PA/purpleair-calibration

# 更新README和CITATION
git add README.md CITATION.cff
git commit -m "Add Zenodo DOI to documentation"
git push origin main
```

---

## ✅ 验证清单

完成后，检查：

- [ ] GitHub Release v1.0.0已创建
- [ ] Zenodo已连接到GitHub仓库
- [ ] DOI已生成（格式: 10.5281/zenodo.XXXXXXX）
- [ ] README.md中的DOI徽章已更新
- [ ] CITATION.cff中添加了DOI
- [ ] 论文main.tex中引用了DOI
- [ ] 所有更改已提交并推送到GitHub

---

## 🎯 最终结果

完成后，您的代码将拥有：

✅ **GitHub仓库**: https://github.com/yunqianz728/purpleair-calibration
✅ **永久DOI**: https://doi.org/10.5281/zenodo.XXXXXXX
✅ **Web演示**: https://huggingface.co/spaces/yunqianz/purpleair-calibration

这三个链接都可以在论文中引用！

---

## 📌 添加GitHub Topics（额外优化）

为了提高仓库的可发现性，建议添加以下topics：

1. 访问: https://github.com/yunqianz728/purpleair-calibration
2. 点击右侧 "About" 旁的齿轮图标 ⚙️
3. 在 "Topics" 输入框中添加：

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

4. 点击 "Save changes"

---

## 🆘 常见问题

### Q1: Zenodo没有为我的Release创建DOI怎么办？

**A**: 确保：
1. Zenodo已连接到您的仓库（开关是绿色的）
2. 创建了新的Release（不是draft）
3. 等待5-10分钟让Zenodo处理

如果还是没有，尝试创建新的Release（如v1.0.1）。

### Q2: 我想更新已发布的代码怎么办？

**A**: 创建新的Release版本：
- Bug修复: v1.0.1, v1.0.2
- 新功能: v1.1.0, v1.2.0
- 重大更新: v2.0.0

每个版本都会在Zenodo上获得独立的DOI，但主DOI会指向最新版本。

### Q3: DOI徽章显示错误怎么办？

**A**: 检查：
1. DOI格式正确: `10.5281/zenodo.XXXXXXX`
2. 徽章URL格式: `https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg`
3. GitHub可能需要几分钟缓存新的徽章

### Q4: 我可以在论文接受前创建DOI吗？

**A**: 可以！建议：
- 论文投稿时：创建v1.0.0（预印本版本）
- 论文接受后：创建v1.1.0（发表版本）
- 在Release说明中注明论文状态

---

## 📧 需要帮助？

如果遇到问题：
1. **Zenodo帮助**: https://help.zenodo.org/
2. **GitHub Releases文档**: https://docs.github.com/en/repositories/releasing-projects-on-github
3. **联系我们**: lianglu@berkeley.edu

---

**创建日期**: 2026-02-02
**最后更新**: 2026-02-02
**状态**: ✅ 准备就绪
