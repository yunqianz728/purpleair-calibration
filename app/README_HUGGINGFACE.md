---
title: PurpleAir Temperature Calibration
emoji: 🌡️
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: "1.31.0"
app_file: app.py
pinned: true
license: mit
tags:
  - temperature
  - calibration
  - machine-learning
  - climate
  - sensors
  - environmental-science
---

# 🌡️ PurpleAir Temperature Calibration

Accurate temperature monitoring for heat exposure research using machine learning calibration.

## 📊 Overview

This application calibrates PurpleAir temperature sensor readings using trained XGBoost models. It reduces measurement errors by **90%**, achieving an overall RMSE of **1.43°C**.

### Key Features

- ✅ **90% error reduction** compared to uncalibrated sensors
- ✅ **Temperature-stratified models** (Cold/Moderate/Hot conditions)
- ✅ **63 engineered features** including temporal dynamics
- ✅ **Automatic ERA5 data integration** for meteorological variables
- ✅ **Real-time calibration** with CSV upload
- ✅ **Validated on 2,682 sensors** across 31 U.S. states (2018-2022)

## 🎯 Performance

| Temperature Range | RMSE | Improvement |
|------------------|------|-------------|
| **Cold** (<10°C) | 1.52°C | 88% reduction |
| **Moderate** (10-30°C) | 1.38°C | 91% reduction |
| **Hot** (>30°C) | 1.45°C | 89% reduction |
| **Overall** | 1.43°C | 90% reduction |

## 🚀 How to Use

### 1. Prepare Your Data

#### 📍 Spatial Model (31 features)

**Required columns:**
- `timestamp` - Date/time (YYYY-MM-DD HH:MM:SS)
- `temperature` - Current sensor temp (°F or °C)
- `humidity` - Relative humidity (%)
- `latitude` - Sensor latitude (-90 to 90)
- `longitude` - Sensor longitude (-180 to 180)

**Optional** (improve accuracy):
- `elevation` - Meters above sea level
- `tree_canopy_cover` - Tree cover percentage
- `life` or `age` - Days since deployment

**Example:**
```csv
timestamp,temperature,humidity,latitude,longitude,elevation,life
2024-01-15 12:00:00,68.5,45.2,37.7749,-122.4194,15,450
```

#### ⏱️ Temporal Model (61 features - Higher Accuracy)

**All Spatial columns PLUS:**
- **Historical data**: Include at least **6 hours of prior readings** before each target timestamp
- Upload CSV with multiple rows (one per hour) for the same sensor

**Example (time series):**
```csv
timestamp,temperature,humidity,latitude,longitude,elevation,life
2024-01-15 06:00:00,65.2,48.5,37.7749,-122.4194,15,450
2024-01-15 07:00:00,66.8,47.1,37.7749,-122.4194,15,450
2024-01-15 08:00:00,67.3,46.8,37.7749,-122.4194,15,450
2024-01-15 09:00:00,67.9,45.9,37.7749,-122.4194,15,450
2024-01-15 10:00:00,68.1,45.5,37.7749,-122.4194,15,450
2024-01-15 11:00:00,68.4,45.3,37.7749,-122.4194,15,450
2024-01-15 12:00:00,68.5,45.2,37.7749,-122.4194,15,450  ← Target
```

**Auto-derived from your data:**
- ✅ Lagged features (temp/humidity 1-6h ago)
- ✅ Rolling statistics (moving averages, std dev)
- ✅ Cumulative radiation, temperature trends
- ✅ Hot/cold persistence counters

**Auto-fetched:**
- ✅ ERA5 meteorological data (solar radiation, wind, pressure, etc.)
- ✅ Derived features (dewpoint, VPD, time encodings, interaction terms)

### 2. Upload and Calibrate

1. Click "Upload PurpleAir CSV file"
2. Select column mappings
3. Choose temperature unit
4. Click "Start Calibration"
5. Download calibrated results

## 🔬 Methodology

This tool implements the calibration framework from:

**"Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research"**
Zhang, Y., Rong, Y., & Liang, L. (2025)

### Calibration Approach

1. **Temperature Stratification**: Three specialized XGBoost models for different thermal regimes
2. **Temporal Features**: 12-hour sensor thermal history and dynamics
3. **Meteorological Integration**: Automatic ERA5 data fetching (solar radiation, humidity, wind, etc.)
4. **Feature Engineering**: 63 features capturing sensor physics and environmental conditions

### Why This Works

PurpleAir sensors suffer from solar heating bias due to inadequate radiation shielding. Our calibration:
- Captures sensor thermal inertia (how sensors heat up and cool down)
- Accounts for varying bias across temperature ranges
- Uses meteorological data to predict and correct systematic errors

## 📚 Citation

If you use this tool in your research, please cite:

```bibtex
@article{zhang2025purpleair,
  title={Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research},
  author={Zhang, Yunqian and Rong, Yan and Liang, Lu},
  journal={[Journal Name]},
  year={2025},
  doi={10.5281/zenodo.18463819}
}
```

## 🔗 Resources

- **Code Repository**: [GitHub](https://github.com/yunqianz728/purpleair-calibration)
- **Archived Code**: [Zenodo DOI: 10.5281/zenodo.18463819](https://doi.org/10.5281/zenodo.18463819)
- **ERA5 Data Archive**: [Zenodo DOI: 10.5281/zenodo.18485026](https://doi.org/10.5281/zenodo.18485026)
- **Paper**: [DOI: 10.5281/zenodo.18463819](https://doi.org/10.5281/zenodo.18463819)

## 📖 Documentation

### Data Requirements

- **Time Range**: 2022-01-01 to 2024-12-31 (ERA5 data availability)
- **Location**: Continental United States (CONUS) recommended
- **Temporal Resolution**: Hourly data works best
- **File Format**: CSV with standard column names

### Limitations

- Requires internet connection to fetch ERA5 data
- First-time calibration may take longer (ERA5 download)
- Calibration accuracy depends on data quality and completeness

## 🛠️ Technical Details

### Models

- **Algorithm**: XGBoost (Gradient Boosting)
- **Model Size**: 44 MB (3 models)
- **Features**: 63 engineered features
- **Training Data**: 797,744 hourly observations from 98 sensors

### Processing Steps

1. Validate input data
2. Fetch ERA5 meteorological data for location/time
3. Calculate 63 features (spatial + temporal)
4. Apply temperature-stratified model
5. Return calibrated temperature with uncertainty estimates

## 👥 Authors

- **Yunqian Zhang** - UC Berkeley / Beijing Normal University
- **Yan Rong** - University of Illinois Chicago
- **Lu Liang** (Corresponding Author) - UC Berkeley

## 📧 Contact

- Email: lianglu@berkeley.edu
- Issues: [GitHub Issues](https://github.com/yunqianz728/purpleair-calibration/issues)

## 📄 License

MIT License - See repository for details

---

**Developed by**: Yunqian Zhang & Lu Liang
**Institution**: University of California, Berkeley
**Last Updated**: February 2025
