# Jupyter Notebooks

This directory contains interactive Jupyter notebooks demonstrating the complete workflow for PurpleAir temperature calibration.

## Notebooks

### 01_data_exploration.ipynb
**Purpose**: Explore and visualize the calibration dataset

**Contents**:
- Load paired sensor-station data
- Temporal distribution analysis (monthly/hourly patterns)
- Spatial distribution across climate zones
- Temperature distribution histograms
- Uncalibrated error analysis (bias, diurnal patterns)
- Correlation analysis between features

**Key Outputs**:
- Summary statistics tables
- Geographic distribution maps
- Time series plots
- Error distribution histograms

**Run time**: ~5 minutes

---

### 02_feature_analysis.ipynb
**Purpose**: Analyze feature importance using SHAP values

**Contents**:
- Load trained models (Temporal-TempStrat)
- Calculate SHAP values for each temperature stratum
- Generate SHAP summary plots
- Feature importance rankings
- Feature interaction analysis
- Partial dependence plots

**Key Outputs**:
- SHAP summary plots (Figure 5 from paper)
- Feature importance tables
- Interaction plots

**Run time**: ~15 minutes

---

### 03_model_training.ipynb
**Purpose**: Train calibration models from scratch

**Contents**:
- Load and preprocess data
- Feature engineering (63 features)
- Data splitting (train/val/test)
- Hyperparameter optimization (Bayesian with Optuna)
- Model training for each stratum
- Cross-validation
- Model comparison (XGBoost vs CatBoost vs LightGBM)

**Key Outputs**:
- Trained model files
- Hyperparameter optimization history
- Training curves
- Model comparison tables

**Run time**: ~2-4 hours (depending on n_trials)

**Requirements**: 16 GB RAM recommended

---

### 04_evaluation.ipynb
**Purpose**: Evaluate model performance comprehensively

**Contents**:
- Load test set and trained models
- Calculate performance metrics (MAE, RMSE, R²)
- Temporal error analysis (monthly, hourly patterns)
- Spatial error analysis (by climate zone, state)
- Stratum-specific performance
- Comparison with baselines (uncalibrated, linear regression)
- Statistical significance tests

**Key Outputs**:
- Performance metrics tables (Table 3 from paper)
- Error distribution plots (Figure 3 from paper)
- Geographic error maps (Figure 4 from paper)
- Performance comparison charts

**Run time**: ~10 minutes

---

### 05_visualization.ipynb
**Purpose**: Generate publication-quality figures

**Contents**:
- Figure 1: Dataset spatial distribution and climate zones
- Figure 2: Workflow diagram
- Figure 3: Temporal error patterns (monthly/hourly)
- Figure 4: Geographic error distribution
- Figure 5: SHAP feature importance
- Supplementary figures

**Key Outputs**:
- High-resolution figures (300 DPI, PDF/PNG)
- Figures matching paper exactly

**Run time**: ~5 minutes

---

## Usage

### Starting Jupyter Lab
```bash
# Activate environment
conda activate purpleair-calib

# Start Jupyter Lab
jupyter lab
```

### Running Notebooks in Order
1. Start with `01_data_exploration.ipynb` to understand the dataset
2. Proceed to `02_feature_analysis.ipynb` for feature insights
3. (Optional) Train models with `03_model_training.ipynb`
4. Evaluate performance with `04_evaluation.ipynb`
5. Generate figures with `05_visualization.ipynb`

### Data Requirements

Most notebooks require pre-processed data:
- `data/processed/features.csv`: Feature-engineered dataset
- `data/processed/test_set.csv`: Held-out test set
- `results/models/`: Trained model files

Download processed data from:
- Hugging Face: https://huggingface.co/spaces/yunqianz/purpleair-calibration
- Zenodo: DOI 10.xxxx/zenodo.xxxxxx

### Notebook Tips

**Memory Management**:
```python
# Clear variables when done
%reset -f

# Monitor memory usage
%load_ext memory_profiler
%memit command
```

**Parallel Processing**:
```python
# Use all CPU cores for faster computation
from joblib import Parallel, delayed
import multiprocessing

n_cores = multiprocessing.cpu_count()
```

**Plotting Settings**:
```python
# Set matplotlib defaults for publication-quality figures
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'sans-serif'
sns.set_style('whitegrid')
```

## Exporting Notebooks

**Convert to Python script**:
```bash
jupyter nbconvert --to script notebook.ipynb
```

**Convert to HTML**:
```bash
jupyter nbconvert --to html notebook.ipynb
```

**Convert to PDF**:
```bash
jupyter nbconvert --to pdf notebook.ipynb
```

## Troubleshooting

**Kernel crashes**:
- Reduce batch size or use data subsampling
- Increase available RAM
- Use `dask` for out-of-core computation

**Missing data**:
- Download from Hugging Face or Zenodo
- Or generate from scratch using `data/` scripts

**Import errors**:
- Ensure environment is activated: `conda activate purpleair-calib`
- Reinstall packages: `pip install -r requirements.txt`

## Contributing

To add new notebooks:
1. Follow naming convention: `##_descriptive_name.ipynb`
2. Include docstring at top explaining purpose
3. Add clear markdown sections
4. Test with clean kernel restart
5. Update this README

## Support

Questions about notebooks? Open an issue:
https://github.com/yourusername/purpleair-calibration/issues
