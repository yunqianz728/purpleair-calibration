# PurpleAir Temperature Sensor Calibration

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18463819.svg)](https://doi.org/10.5281/zenodo.18463819)
[![Hugging Face](https://img.shields.io/badge/🤗-Demo-yellow)](https://huggingface.co/spaces/yunqianz/purpleair-calibration)

## Overview

This repository contains the complete code and methodology for nationwide calibration of PurpleAir temperature sensors using machine learning. The framework addresses systematic warm bias in low-cost sensors, enabling accurate hyperlocal temperature monitoring for heat-health research, urban climate studies, and environmental justice applications.

**Paper**: *Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research*
**Authors**: Yunqian Zhang, Yan Rong, Lu Liang
**Contact**: lianglu@berkeley.edu

## Key Features

- **High Accuracy**: Mean absolute error (MAE) of 0.38-0.53°C across diverse climatic conditions
- **90% Error Reduction**: Compared to uncalibrated sensors (uncalibrated MAE: 5.4°C ± 6.7°C)
- **Temperature-Based Stratification**: Outperforms climate-zone stratification by 32-51%
- **Temporal Features**: Captures sensor thermal memory and radiation dynamics
- **National Scale**: Validated across 31 U.S. states, 797,744 hourly observations
- **Real-time Deployment**: Millisecond-level prediction latency, 45 MB model size
- **🌐 User-Friendly Web App**: [Click here to use the web interface](app/) - No coding required!
- **Open Access**: Free web interface available at [Hugging Face](https://huggingface.co/spaces/yunqianz/purpleair-calibration)

## Problem Statement

PurpleAir sensors, while offering unprecedented spatial coverage (15,000+ sensors nationwide), suffer from severe temperature bias:
- Average overheating bias: **5.4°C** (±6.7°C)
- Nighttime bias: **3.5°C**
- Peak daytime bias: **13.5°C** during solar radiation periods

This bias renders uncalibrated data unsuitable for heat-health monitoring or climate research.

## Solution: Temporal-TempStrat Model

Our best-performing model combines:

1. **Temperature Stratification**: Separate models for cold/moderate/hot thermal regimes
2. **Temporal Features (61 total)**:
   - Lagged variables: Historical temp, humidity, radiation (1-6 hours)
   - Rolling statistics: Moving averages, standard deviations over 3-12 hour windows
   - Cumulative radiation: Solar energy accumulation over 3-6 hours
   - Change indicators: Temperature rise/fall rates and acceleration
   - Thermal persistence: Heat wave and cold spell counters

3. **Spatial Features (31 total)**:
   - Sensor measurements: Temperature, humidity, operational lifetime
   - ERA5 meteorology: Solar/thermal radiation, wind, precipitation
   - Site characteristics: Elevation, tree canopy cover, coordinates
   - Engineered terms: Polynomial and interaction terms

4. **Gradient Boosting**: XGBoost, CatBoost, and LightGBM with Bayesian hyperparameter optimization

## Performance Summary

| Configuration | Temperature Range | MAE (°C) | RMSE (°C) | Improvement vs. Baseline |
|--------------|-------------------|----------|-----------|-------------------------|
| **Temporal-TempStrat** | Cold | 0.38 | 0.57 | **-37%** |
| **Temporal-TempStrat** | Hot | 0.46 | 0.69 | **-29%** |
| **Temporal-TempStrat** | Moderate | 0.53 | 0.74 | **-20%** |
| Temporal-National | All | 0.77 | 1.08 | Baseline |
| Spatial-National | All | 1.06 | 1.44 | Baseline |

## 🚀 Quick Start

### For Non-Programmers: Use the Web App! 🌐

**✨ FULLY FUNCTIONAL** - Now with real XGBoost models and automatic ERA5 integration!

**No installation, no coding, no command line needed!**

1. **Run Locally** (Recommended):
   ```bash
   cd app/
   pip install -r requirements.txt
   streamlit run app.py
   ```
   Opens in your browser at `localhost:8501`

2. **Or deploy for free**:
   - See [app/README.md](app/README.md) for Streamlit Cloud / Hugging Face deployment

**What the app does automatically**:
- 🌡️ **Temperature-Stratified Calibration**: Uses 3 specialized XGBoost models (Cold/Moderate/Hot)
- 🌍 **Automatic ERA5 Integration**: Fetches meteorological data for your location/time
- 🔧 **63-Feature Engineering**: Calculates temporal, spatial, and meteorological features
- 📊 **Interactive Visualizations**: Time series plots, distributions, regime analysis
- 📥 **Complete Results**: Download calibrated data + detailed reports

**What you need to provide**:
- ✅ Simple CSV with 5 columns: `timestamp`, `temperature`, `humidity`, `latitude`, `longitude`
- ✅ Data must be within 2022-2024 (ERA5 coverage)
- ✅ That's it! Everything else is automatic.

**Performance**:
- RMSE: 1.43°C overall
- Processing: ~30 seconds per 1000 records
- Tested and working: ✅ All systems operational

**Full Web App Guide**: [app/README.md](app/README.md)

---

### For Programmers: Python Package

## Installation

### Prerequisites
- Python 3.8 or higher
- conda (recommended) or pip

### Option 1: Conda Environment (Recommended)
```bash
# Clone the repository
git clone https://github.com/yunqianz728/purpleair-calibration.git
cd purpleair-calibration

# Create and activate conda environment
conda env create -f environment.yml
conda activate purpleair-calib
```

### Option 2: pip Installation
```bash
# Clone the repository
git clone https://github.com/yunqianz728/purpleair-calibration.git
cd purpleair-calibration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Development Installation
```bash
# For development with editable install
pip install -e .
```

## Quick Start

### 1. Download Pre-trained Models
```bash
# Download models from Hugging Face
python scripts/download_models.py
```

### 2. Calibrate PurpleAir Data
```python
from models.calibration import TemporalTempStratCalibrator
import pandas as pd

# Load your PurpleAir data
data = pd.read_csv('your_purpleair_data.csv')

# Initialize calibrator
calibrator = TemporalTempStratCalibrator()

# Perform calibration
calibrated_data = calibrator.calibrate(data)

# Save results
calibrated_data.to_csv('calibrated_temperature.csv', index=False)
```

### 3. Use Web Interface (No Coding Required)
Visit our [Hugging Face Demo](https://huggingface.co/spaces/yunqianz/purpleair-calibration) to calibrate data directly in your browser.

## Repository Structure

```
purpleair-calibration/
├── data/                          # Data processing scripts
│   ├── download_purpleair.py     # PurpleAir API data retrieval
│   ├── download_era5.py          # ERA5 reanalysis data download
│   ├── download_hadisd.py        # HadISD reference station data
│   ├── match_sensors.py          # Sensor-station spatial-temporal matching
│   └── feature_engineering.py    # Generate 61 predictive features
│
├── models/                        # Model training and inference
│   ├── calibration.py            # Main calibration interface
│   ├── train_xgboost.py          # XGBoost training script
│   ├── train_catboost.py         # CatBoost training script
│   ├── train_lightgbm.py         # LightGBM training script
│   ├── hyperparameter_opt.py     # Bayesian optimization
│   └── ensemble.py               # Voting ensemble models
│
├── notebooks/                     # Jupyter notebooks
│   ├── 01_data_exploration.ipynb # Dataset analysis
│   ├── 02_feature_analysis.ipynb # Feature importance (SHAP)
│   ├── 03_model_training.ipynb   # Model development
│   ├── 04_evaluation.ipynb       # Performance evaluation
│   └── 05_visualization.ipynb    # Result visualization
│
├── figures/                       # Figure generation scripts
│   ├── generate_figure1.py       # Spatial distribution map
│   ├── generate_figure2.py       # Workflow diagram
│   ├── generate_figure3.py       # Temporal error patterns
│   ├── generate_figure4.py       # Geographic error distribution
│   └── generate_figure5.py       # SHAP feature importance
│
├── results/                       # Output directory (gitignored)
│   ├── models/                   # Trained model files
│   ├── predictions/              # Calibration outputs
│   └── evaluation/               # Performance metrics
│
├── docs/                          # Documentation
│   ├── API.md                    # API documentation
│   ├── USAGE.md                  # Detailed usage guide
│   ├── FAQ.md                    # Frequently asked questions
│   └── TROUBLESHOOTING.md        # Common issues and solutions
│
├── tests/                         # Unit tests
│   ├── test_data_processing.py
│   ├── test_features.py
│   └── test_models.py
│
├── config/                        # Configuration files
│   ├── model_config.yaml         # Model hyperparameters
│   └── data_config.yaml          # Data processing settings
│
├── scripts/                       # Utility scripts
│   ├── download_models.py        # Download pre-trained models
│   └── run_calibration.py        # End-to-end calibration pipeline
│
├── requirements.txt               # Python dependencies
├── environment.yml                # Conda environment specification
├── setup.py                       # Package installation
├── LICENSE                        # MIT License
├── CITATION.cff                   # Citation file format
├── CONTRIBUTING.md                # Contribution guidelines
├── .gitignore                     # Git ignore patterns
└── README.md                      # This file
```

## Data Availability

### Input Data Sources

1. **PurpleAir Sensor Data**
   - Source: [PurpleAir API](https://api.purpleair.com/)
   - Variables: Temperature, humidity, coordinates, elevation, deployment date
   - Temporal coverage: June 2022 - December 2024
   - Spatial coverage: 98 sensors across 31 U.S. states

2. **ERA5 Reanalysis Data**
   - Source: [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/)
   - Variables: Solar radiation (SSRD), thermal radiation (STRD), sensible heat flux (SSHF), wind (u10/v10), precipitation
   - Resolution: 0.1° (most variables), 0.25° (wind)
   - Temporal coverage: Hourly, 2022-2024

3. **HadISD Reference Stations**
   - Source: [Met Office Hadley Centre](https://www.metoffice.gov.uk/hadobs/hadisd/)
   - Variables: Air temperature (quality-controlled)
   - Stations: 69 HadISD stations paired with PurpleAir sensors
   - Matching criteria: <3 km distance, <20 m elevation difference, <20% tree canopy cover difference

4. **Auxiliary Data**
   - Tree Canopy Cover: [Global Forest Change](https://earthenginepartners.appspot.com/science-2013-global-forest)
   - Elevation: [SRTM 30m DEM](https://www2.jpl.nasa.gov/srtm/)
   - Climate Zones: [Köppen-Geiger Classification](http://koeppen-geiger.vu-wien.ac.at/)

### Processed Training Data

All paired sensor-station training data, feature-engineered datasets, and model training scripts are available at:
- **Hugging Face**: [https://huggingface.co/spaces/yunqianz/purpleair-calibration](https://huggingface.co/spaces/yunqianz/purpleair-calibration)
- **Zenodo**: [DOI: 10.xxxx/zenodo.xxxxxx](https://doi.org/10.xxxx/zenodo.xxxxxx) (coming soon)

## Model Architecture

### Feature Engineering Pipeline

The calibration model uses **63 total features** (61 training + 2 stratification indicators):

#### Spatial Features (31)
- **Primary Measurements**: Sensor temperature, humidity, operational lifetime
- **ERA5 Meteorology**: Solar/thermal radiation, sensible heat flux, precipitation, wind components
- **Derived Meteorology**: Wind speed/direction, dewpoint, vapor pressure deficit
- **Site Characteristics**: Latitude, longitude, elevation, tree canopy cover
- **Solar Geometry**: Hour of day
- **Engineered Terms**: Polynomial (temp², humidity²) and interaction terms (temp×humidity, temp×age)

#### Temporal Features (30)
All temporal features use **only historical data** to enable real-time prediction:

- **Lagged Variables (11)**: Temperature (1-6h ago), humidity (1-3h ago), radiation (1-2h ago)
- **Rolling Statistics (10)**: Moving averages, standard deviations, temperature ranges, linear trends over 3-12h windows
- **Cumulative Radiation (3)**: Total solar energy over 3-6h plus hourly change rate
- **Change Indicators (4)**: Temperature rise/fall rates over 1-3h plus acceleration
- **Thermal Persistence (2)**: Consecutive hour counters for hot (>75th percentile) and cold (<25th percentile) conditions

### Stratification Strategy

**Temperature-Based Stratification** (Recommended):
- **Cold**: Temperature < 25th percentile (climate-zone-specific)
- **Moderate**: 25th ≤ Temperature ≤ 75th percentile
- **Hot**: Temperature > 75th percentile

Each stratum trains a separate XGBoost model optimized for its thermal regime.

**Alternative**: Temporal-National (single model, no stratification) for simpler deployment.

### Hyperparameter Optimization

Bayesian optimization (Optuna framework) with 20 trials per model:
- **Objective**: Minimize weighted MAE on validation set
- **Search Space**: Learning rate, max depth, number of estimators, subsample ratio, colsample_bytree, regularization parameters
- **Final Training**: Retrain on combined training+validation sets (80%) after hyperparameter selection

## Usage Examples

### Example 1: Calibrate Real-time PurpleAir Data
```python
from models.calibration import TemporalTempStratCalibrator
from data.download_purpleair import fetch_purpleair_data
from data.download_era5 import fetch_era5_data
import pandas as pd

# Fetch PurpleAir data for a specific sensor
sensor_id = 123456
pa_data = fetch_purpleair_data(
    sensor_id=sensor_id,
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# Fetch corresponding ERA5 data
era5_data = fetch_era5_data(
    lat=pa_data['latitude'].iloc[0],
    lon=pa_data['longitude'].iloc[0],
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# Merge datasets
data = pd.merge(pa_data, era5_data, on='timestamp')

# Initialize calibrator
calibrator = TemporalTempStratCalibrator(model_path='results/models/temporal_tempstrat')

# Calibrate
calibrated = calibrator.calibrate(data)

print(f"Original temperature: {data['temperature'].mean():.2f}°C")
print(f"Calibrated temperature: {calibrated['temperature_calibrated'].mean():.2f}°C")
print(f"Estimated bias: {(data['temperature'] - calibrated['temperature_calibrated']).mean():.2f}°C")
```

### Example 2: Train Custom Model
```python
from models.train_xgboost import train_temporal_tempstrat
from data.feature_engineering import engineer_features
import pandas as pd

# Load paired sensor-station data
data = pd.read_csv('data/processed/paired_sensor_station_data.csv')

# Engineer features
features = engineer_features(data)

# Train model with Bayesian optimization
model, performance = train_temporal_tempstrat(
    features=features,
    n_trials=20,
    test_size=0.2,
    val_size=0.16,
    save_path='results/models/my_custom_model'
)

print(f"Test MAE: {performance['test_mae']:.3f}°C")
print(f"Test RMSE: {performance['test_rmse']:.3f}°C")
print(f"Test R²: {performance['test_r2']:.3f}")
```

### Example 3: Batch Calibration of Multiple Sensors
```python
from models.calibration import batch_calibrate
import pandas as pd

# Load data for multiple sensors
sensor_data = pd.read_csv('data/multiple_sensors.csv')

# Batch calibration
calibrated = batch_calibrate(
    data=sensor_data,
    sensor_id_column='sensor_id',
    model_type='temporal_tempstrat',
    n_jobs=4  # Parallel processing
)

# Save results
calibrated.to_csv('results/predictions/batch_calibrated.csv', index=False)
```

## Performance Metrics

### Error Reduction by Time Period

| Metric | Uncalibrated | Calibrated (Temporal-TempStrat) | Improvement |
|--------|--------------|--------------------------------|-------------|
| **Annual MAE** | 5.4°C | 0.48°C | **91.1%** |
| **Summer MAE** | 7.1°C | 0.52°C | **92.7%** |
| **Winter MAE** | 6.0°C | 0.48°C | **92.0%** |
| **Daytime MAE (12-14h)** | 13.5°C | 0.50°C | **96.3%** |
| **Nighttime MAE (00-06h)** | 3.5°C | 0.43°C | **87.7%** |

### Regional Performance

| Climate Zone | MAE (°C) | RMSE (°C) | Sample Size |
|--------------|----------|-----------|-------------|
| Continental | 0.43 | 0.62 | 245,000 |
| Temperate | 0.48 | 0.68 | 312,000 |
| Arid | 0.52 | 0.73 | 240,744 |

## Key Findings

### 1. Temporal Features are Critical
- Temporal models outperform spatial-only models by **26.2%**
- Sensor thermal memory effects account for **54-69%** of feature importance
- 6-hour initialization period is essential for optimal performance

### 2. Temperature Stratification Outperforms Climate-Zone Stratification
- **32-51%** better than national baseline
- **19-37%** better than unstratified models
- Handles seasonal variability without retraining

### 3. Physical Mechanisms Revealed by SHAP Analysis
- **Cold conditions**: Thermal inertia dominates (12h moving averages most important)
- **Moderate conditions**: Balanced contribution from lagged values and rolling statistics
- **Hot conditions**: Radiation variables increase to 11% importance (SSHF, STRD, cumulative radiation)

### 4. Real-world Deployment Characteristics
- **Model size**: 45 MB per stratum (135 MB total)
- **Memory usage**: ~100 MB during inference
- **Prediction latency**: <5 ms per sample
- **Initialization**: 6 hours of historical data required for temporal features

## Citation

If you use this code or methodology in your research, please cite:

```bibtex
@article{zhang2025purpleair,
  title={Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research},
  author={Zhang, Yunqian and Rong, Yan and Liang, Lu},
  journal={[Journal Name]},
  year={2025},
  doi={10.xxxx/xxxxxx},
  note={Submitted for publication}
}
```

**APA Format**:
Zhang, Y., Rong, Y., & Liang, L. (2025). Nationwide calibration of PurpleAir temperature sensors for heat exposure research. *[Journal Name]*. https://doi.org/10.xxxx/xxxxxx

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Key Points:
- ✅ Free to use for academic and commercial purposes
- ✅ Attribution required (cite our paper)
- ✅ No warranty provided
- ✅ Open-source contributions welcome

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution:
- Additional sensor platform support (Netatmo, Ambient Weather, Davis Instruments)
- Integration with real-time weather APIs (NOAA HRRR, ECMWF IFS)
- Optimization for edge devices (Raspberry Pi, Arduino)
- Translation to other programming languages (R, Julia)
- Documentation improvements

## Acknowledgments

We thank:
- **Justin Tse** for guidance on PurpleAir API and data access protocols
- **PurpleAir Community** for maintaining the sensor network and making data publicly available
- **HadISD Team** for curating high-quality reference station data
- **Copernicus Climate Change Service** for ERA5 reanalysis data
- **NASA** for SRTM elevation data
- **University of Maryland** for Global Forest Change dataset

## Contact

- **Corresponding Author**: Lu Liang (lianglu@berkeley.edu)
- **Lead Developer**: Yunqian Zhang
- **Issues**: [GitHub Issues](https://github.com/yunqianz728/purpleair-calibration/issues)
- **Web Interface**: [Hugging Face Demo](https://huggingface.co/spaces/yunqianz/purpleair-calibration)

## Related Publications

- Anderson et al. (2009). Weather-related mortality: How heat, cold, and heat waves affect mortality in the United States. *Epidemiology*, 20(2), 205-213.
- Considine et al. (2023). PurpleAir air quality sensor network. *Environmental Science & Technology*.
- Hersbach et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, 146, 1999-2049.
- Hoffman et al. (2020). Effects of historical housing policies on resident exposure to intra-urban heat. *Climate*, 8(1), 12.

## Changelog

### Version 1.0.0 (2025-01-XX)
- Initial release
- Temporal-TempStrat model (MAE 0.38-0.53°C)
- Temporal-National baseline model (MAE 0.77°C)
- Complete training pipeline with Bayesian optimization
- Web interface deployment on Hugging Face
- Comprehensive documentation and examples

---

**Last Updated**: February 2025
**Repository Status**: Active Development
**Paper Status**: Under Review
