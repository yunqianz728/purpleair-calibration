# Detailed Usage Guide

This guide provides comprehensive instructions for using the PurpleAir temperature calibration framework.

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Data Preparation](#data-preparation)
4. [Feature Engineering](#feature-engineering)
5. [Model Training](#model-training)
6. [Calibration](#calibration)
7. [Evaluation](#evaluation)
8. [Advanced Usage](#advanced-usage)

---

## Installation

### Prerequisites
- Python 3.8 or higher
- 8 GB RAM (16 GB recommended for training)
- 2 GB free disk space

### Installation Steps

**Option 1: Conda (Recommended)**
```bash
git clone https://github.com/yourusername/purpleair-calibration.git
cd purpleair-calibration
conda env create -f environment.yml
conda activate purpleair-calib
```

**Option 2: pip**
```bash
git clone https://github.com/yourusername/purpleair-calibration.git
cd purpleair-calibration
pip install -r requirements.txt
```

**Option 3: Package Installation**
```bash
pip install purpleair-calibration
```

### Verify Installation
```python
import xgboost
import pandas as pd
from models.calibration import TemporalTempStratCalibrator

print("Installation successful!")
```

---

## Quick Start

### 1. Download Pre-trained Models
```bash
python scripts/download_models.py
```

This downloads models to `results/models/`:
- `xgboost_cold.joblib`: Cold stratum model
- `xgboost_moderate.joblib`: Moderate stratum model
- `xgboost_hot.joblib`: Hot stratum model
- `metadata.json`: Model configuration

### 2. Prepare Your Data
Your data must include:
- PurpleAir sensor readings (temperature, humidity)
- ERA5 meteorological variables
- Sensor metadata (location, elevation)

Example data structure:
```python
import pandas as pd

data = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
    'temperature': [25.0] * 100,  # PurpleAir sensor temperature (°C)
    'humidity': [50.0] * 100,     # Relative humidity (%)
    'latitude': [40.0] * 100,     # Sensor latitude
    'longitude': [-120.0] * 100,  # Sensor longitude
    'elevation': [100.0] * 100,   # Sensor elevation (m)
    # ERA5 variables
    'SSRD': [0.0] * 100,  # Solar radiation (J/m²)
    'STRD': [0.0] * 100,  # Thermal radiation (J/m²)
    'SSHF': [0.0] * 100,  # Sensible heat flux (J/m²)
    'u10': [2.0] * 100,   # U-wind component (m/s)
    'v10': [1.0] * 100,   # V-wind component (m/s)
    'precipitation': [0.0] * 100,  # Total precipitation (m)
})
```

### 3. Calibrate
```python
from models.calibration import TemporalTempStratCalibrator

# Initialize calibrator
calibrator = TemporalTempStratCalibrator(
    model_path='results/models'
)

# Calibrate your data
calibrated = calibrator.calibrate(data)

# View results
print(calibrated[['timestamp', 'temperature', 'temperature_calibrated', 'temperature_bias']].head())
```

---

## Data Preparation

### Downloading PurpleAir Data

**Using API directly:**
```python
from data.download_purpleair import PurpleAirDownloader

downloader = PurpleAirDownloader(api_key='YOUR_API_KEY')

# Download single sensor
data = downloader.fetch_sensor_history(
    sensor_id=123456,
    start_date='2024-01-01',
    end_date='2024-01-31'
)
```

**Using command line:**
```bash
python data/download_purpleair.py \
  --sensor-id 123456 \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output data/raw/purpleair_123456.csv
```

### Downloading ERA5 Data

**Prerequisites:**
1. Register at https://cds.climate.copernicus.eu/
2. Get API key
3. Create `~/.cdsapirc`:
   ```
   url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR_UID:YOUR_API_KEY
   ```

**Download ERA5:**
```python
from data.download_era5 import fetch_era5_data

era5_data = fetch_era5_data(
    lat=40.0,
    lon=-120.0,
    start_date='2024-01-01',
    end_date='2024-01-31'
)
```

**Command line:**
```bash
python data/download_era5.py \
  --lat 40.0 \
  --lon -120.0 \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output data/raw/era5_data.csv
```

### Merging Datasets
```python
import pandas as pd

# Load data
sensor_data = pd.read_csv('data/raw/purpleair_123456.csv')
era5_data = pd.read_csv('data/raw/era5_data.csv')

# Merge on timestamp
data = pd.merge(
    sensor_data,
    era5_data,
    on='timestamp',
    how='inner'
)

# Save merged data
data.to_csv('data/processed/merged_data.csv', index=False)
```

---

## Feature Engineering

### Generating All 63 Features

```python
from data.feature_engineering import engineer_features

# Generate features
features = engineer_features(
    sensor_data=sensor_data,
    era5_data=era5_data,
    climate_zone='Temperate'  # Optional: 'Arid', 'Temperate', 'Continental'
)

print(f"Generated {len(features.columns)} features")
print(features.columns.tolist())
```

### Feature Groups

**Spatial Features (31 total):**
```python
from data.feature_engineering import FeatureEngineer

engineer = FeatureEngineer(climate_zone='Temperate')

# Primary measurements (3)
# - temperature, humidity, life

# ERA5 meteorology (6)
# - SSRD, STRD, SSHF, precipitation, u10, v10

# Derived meteorology (5)
data = engineer.create_derived_meteorology(data)
# - wind_speed, wind_dir, dewpoint, dewpoint_dep, VPD

# Site characteristics (4)
# - latitude, longitude, elevation, TCC

# Engineered terms (12)
data = engineer.create_engineered_terms(data)
# - temp_squared, humidity_squared, temp_x_humidity, etc.
```

**Temporal Features (30 total):**
```python
# Lagged variables (11)
data = engineer.create_lagged_features(data)
# - temp_1h through temp_6h
# - humidity_1h through humidity_3h
# - SSRD_1h, SSRD_2h

# Rolling statistics (10)
data = engineer.create_rolling_features(data)
# - temp_ma_3h, temp_ma_6h, temp_ma_12h
# - temp_sd_3h, temp_sd_6h, temp_sd_12h
# - temp_range_3h, temp_range_6h
# - temp_trend_3h, temp_trend_6h

# Change indicators (4)
data = engineer.create_change_indicators(data)
# - temp_change_1h, temp_change_2h, temp_change_3h
# - temp_accel

# Cumulative radiation (3)
data = engineer.create_cumulative_radiation(data)
# - SSRD_sum_3h, SSRD_sum_6h, SSRD_change

# Thermal persistence (2)
data = engineer.create_thermal_persistence(data)
# - hot_streak, cold_streak
```

---

## Model Training

### Training Temperature-Stratified Model

```python
from models.train_xgboost import train_temporal_tempstrat
import pandas as pd

# Load processed data with features
data = pd.read_csv('data/processed/features.csv')

# Train model
model, performance = train_temporal_tempstrat(
    data=data,
    target='temperature_error',  # or 'reference_temp'
    n_trials=20,  # Bayesian optimization trials
    test_size=0.2,
    val_size=0.16,
    save_path='results/models/my_model'
)

print(f"Test MAE: {performance['test_mae']:.3f}°C")
print(f"Test RMSE: {performance['test_rmse']:.3f}°C")
print(f"Test R²: {performance['test_r2']:.3f}")
```

### Command Line Training
```bash
python models/train_xgboost.py \
  --data data/processed/features.csv \
  --target temperature_error \
  --model-type temporal_tempstrat \
  --n-trials 20 \
  --output results/models/my_model
```

### Hyperparameter Optimization

```python
from models.hyperparameter_opt import optimize_xgboost
from sklearn.model_selection import train_test_split

# Prepare data
X = features[feature_columns]
y = features['temperature_error']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.2, random_state=42
)

# Optimize
best_params, study = optimize_xgboost(
    X_train, y_train,
    X_val, y_val,
    n_trials=20
)

print(f"Best parameters: {best_params}")
print(f"Best validation MAE: {study.best_value:.3f}°C")
```

---

## Calibration

### Using Pre-trained Models

**Temperature-Stratified Calibration:**
```python
from models.calibration import TemporalTempStratCalibrator

calibrator = TemporalTempStratCalibrator(
    model_path='results/models/temporal_tempstrat'
)

calibrated = calibrator.calibrate(
    data=sensor_data,
    return_uncertainty=True  # Optional: include prediction intervals
)

# Access results
print(calibrated[['timestamp', 'temperature', 'temperature_calibrated']].head())
print(f"Mean bias correction: {calibrated['temperature_bias'].mean():.2f}°C")
```

**National Model (No Stratification):**
```python
from models.calibration import TemporalNationalCalibrator

calibrator = TemporalNationalCalibrator(
    model_path='results/models/temporal_national'
)

calibrated = calibrator.calibrate(data=sensor_data)
```

### Batch Processing Multiple Sensors

```python
from models.calibration import batch_calibrate
import pandas as pd

# Load data for multiple sensors
multi_sensor_data = pd.read_csv('data/processed/multi_sensor.csv')

# Batch calibrate
calibrated = batch_calibrate(
    data=multi_sensor_data,
    sensor_id_column='sensor_id',
    model_type='temporal_tempstrat',
    n_jobs=4  # Parallel processing with 4 cores
)

# Save results
calibrated.to_csv('results/predictions/batch_calibrated.csv', index=False)
```

---

## Evaluation

### Model Performance Metrics

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

def evaluate_calibration(y_true, y_pred):
    """Calculate performance metrics."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)

    print(f"MAE:  {mae:.3f}°C")
    print(f"RMSE: {rmse:.3f}°C")
    print(f"R²:   {r2:.3f}")

    return {'mae': mae, 'rmse': rmse, 'r2': r2}

# Evaluate calibration
if 'reference_temp' in calibrated.columns:
    metrics = evaluate_calibration(
        y_true=calibrated['reference_temp'],
        y_pred=calibrated['temperature_calibrated']
    )
```

### Visualization

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Error distribution
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Before calibration
axes[0].hist(
    calibrated['temperature'] - calibrated['reference_temp'],
    bins=50,
    edgecolor='black'
)
axes[0].set_title('Uncalibrated Error Distribution')
axes[0].set_xlabel('Error (°C)')
axes[0].set_ylabel('Frequency')

# After calibration
axes[1].hist(
    calibrated['temperature_calibrated'] - calibrated['reference_temp'],
    bins=50,
    edgecolor='black',
    color='green'
)
axes[1].set_title('Calibrated Error Distribution')
axes[1].set_xlabel('Error (°C)')

plt.tight_layout()
plt.savefig('results/figures/error_distribution.png', dpi=300)
plt.show()
```

---

## Advanced Usage

### Custom Feature Engineering

```python
from data.feature_engineering import FeatureEngineer

class CustomFeatureEngineer(FeatureEngineer):
    """Extend with custom features."""

    def create_custom_features(self, data):
        """Add domain-specific features."""
        data = data.copy()

        # Example: Add season indicator
        data['month'] = pd.to_datetime(data['timestamp']).dt.month
        data['is_summer'] = data['month'].isin([6, 7, 8]).astype(int)

        # Example: Add urban heat island proxy
        data['urban_intensity'] = 1.0 - data['TCC']  # Inverse of tree cover

        return data

# Use custom engineer
custom_engineer = CustomFeatureEngineer()
data = custom_engineer.create_custom_features(data)
```

### Ensemble Models

```python
from models.ensemble import VotingEnsemble

# Train ensemble
ensemble = VotingEnsemble(
    models=['xgboost', 'catboost', 'lightgbm'],
    weights=[0.4, 0.3, 0.3]  # Optional: weight by validation performance
)

ensemble.fit(X_train, y_train)
predictions = ensemble.predict(X_test)
```

### Feature Importance Analysis

```python
import shap
import matplotlib.pyplot as plt

# Initialize SHAP explainer
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Summary plot
shap.summary_plot(
    shap_values,
    X_test,
    feature_names=feature_names,
    max_display=20
)
plt.savefig('results/figures/shap_summary.png', dpi=300, bbox_inches='tight')
```

### Cross-Validation

```python
from sklearn.model_selection import KFold
import numpy as np

kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = []

for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

    # Train model
    model = xgb.XGBRegressor(**best_params)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_val)
    mae = mean_absolute_error(y_val, y_pred)
    cv_scores.append(mae)

    print(f"Fold {fold+1} MAE: {mae:.3f}°C")

print(f"\nMean CV MAE: {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}°C")
```

---

## Next Steps

- See [FAQ.md](FAQ.md) for common questions
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for debugging help
- See [API.md](API.md) for complete API reference
- Join our [GitHub Discussions](https://github.com/yourusername/purpleair-calibration/discussions)

## Support

For questions or issues:
- Open an issue: https://github.com/yourusername/purpleair-calibration/issues
- Email: lianglu@berkeley.edu
