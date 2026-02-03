# Frequently Asked Questions (FAQ)

## General Questions

### What is PurpleAir?
PurpleAir is a network of low-cost air quality sensors deployed by citizens across the United States and globally. While primarily designed for particulate matter (PM2.5) monitoring, most sensors include temperature and humidity sensors (Bosch BME280 or BME680).

### Why do PurpleAir sensors need calibration for temperature?
PurpleAir sensors exhibit severe warm bias due to:
- Inadequate radiation shielding
- Heat from internal electronics
- Poor ventilation in the plastic enclosure

Uncalibrated sensors show average bias of 5.4°C (±6.7°C), with peak errors exceeding 13.5°C during daytime. This makes raw data unsuitable for heat-health research or climate studies.

### How accurate is the calibration?
Our temperature-stratified model (Temporal-TempStrat) achieves:
- **Cold conditions**: MAE 0.38°C, RMSE 0.57°C
- **Hot conditions**: MAE 0.46°C, RMSE 0.69°C
- **Moderate conditions**: MAE 0.53°C, RMSE 0.74°C
- **Overall**: ~90% error reduction vs. uncalibrated sensors

This accuracy is sufficient for heat-health monitoring, urban heat island studies, and environmental justice applications.

### Which model should I use?
- **Temporal-TempStrat** (recommended): Best accuracy (MAE 0.38-0.53°C) but requires 6 hours of historical data for initialization
- **Temporal-National**: Simpler alternative (MAE 0.77°C), no stratification needed, good for quick deployments

---

## Data Requirements

### What data do I need to calibrate a PurpleAir sensor?
**Sensor data** (from PurpleAir API):
- Temperature (°C)
- Relative humidity (%)
- Sensor coordinates (latitude, longitude)
- Elevation (meters)
- Operational lifetime (days since deployment)

**ERA5 reanalysis data** (from Copernicus CDS):
- Surface solar radiation downward (SSRD)
- Surface thermal radiation downward (STRD)
- Surface sensible heat flux (SSHF)
- 10-meter wind components (u10, v10)
- Total precipitation

**Auxiliary data**:
- Tree canopy cover (from Global Forest Change dataset)
- Köppen climate zone (optional, for stratification)

### How do I get PurpleAir data?
1. **Option 1**: Use our download script
   ```bash
   python data/download_purpleair.py --sensor-id 123456 --start-date 2024-01-01 --end-date 2024-01-31
   ```

2. **Option 2**: PurpleAir API directly
   - Sign up for API key: https://api.purpleair.com/
   - See documentation: https://api.purpleair.com/#api-sensors-get-sensor-history

3. **Option 3**: Use our web interface (no coding required)
   - Visit: https://huggingface.co/spaces/yunqianz/purpleair-calibration

### How do I get ERA5 data?
1. Register at Copernicus Climate Data Store: https://cds.climate.copernicus.eu/
2. Install CDS API and set up credentials
3. Use our download script:
   ```bash
   python data/download_era5.py --lat 40.0 --lon -120.0 --start-date 2024-01-01 --end-date 2024-01-31
   ```

### Can I use real-time data?
Yes, but with caveats:
- **ERA5**: Has ~5-day latency for final products
- **ERA5T** (preliminary): Available within 5 days
- **ERA5-Land**: ~3-day latency
- **NWP forecasts** (HRRR, IFS): Near-real-time but not validated for calibration

For true real-time applications, consider using operational weather forecast models, though performance may differ from ERA5.

### How much historical data do I need?
- **Temporal models**: Minimum 6 hours for initialization (to compute lagged features and rolling statistics)
- **Spatial models**: No historical data required (instant predictions)
- **Training new models**: Recommend at least 3 months of paired sensor-station data

---

## Model Usage

### How do I calibrate my sensor data?
```python
from models.calibration import TemporalTempStratCalibrator
import pandas as pd

# Load your data (must include required features)
data = pd.read_csv('my_sensor_data.csv')

# Initialize calibrator
calibrator = TemporalTempStratCalibrator()

# Calibrate
calibrated = calibrator.calibrate(data)

# Access results
print(calibrated[['temperature', 'temperature_calibrated', 'temperature_bias']])
```

### What if I don't have 6 hours of historical data?
Use the **Spatial-National** or **Spatial-TempStrat** models, which only require instantaneous measurements:
```python
from models.calibration import SpatialNationalCalibrator

calibrator = SpatialNationalCalibrator()
calibrated = calibrator.calibrate(data)
```

Note: Spatial models have higher error (MAE ~1.06°C) compared to temporal models.

### Can I calibrate multiple sensors at once?
Yes, use batch processing:
```python
from models.calibration import batch_calibrate

calibrated = batch_calibrate(
    data=multi_sensor_data,
    sensor_id_column='sensor_id',
    n_jobs=4  # Use 4 CPU cores
)
```

### How do I know which temperature stratum my data falls into?
The model automatically assigns strata based on temperature:
- **Cold**: Temperature < 25th percentile (climate-zone-specific)
- **Moderate**: 25th ≤ Temperature ≤ 75th percentile
- **Hot**: Temperature > 75th percentile

Check the `stratum` column in calibrated output:
```python
print(calibrated['stratum'].value_counts())
```

---

## Performance and Validation

### How was the model validated?
- **Dataset**: 797,744 hourly observations from 98 sensors across 31 U.S. states
- **Time period**: June 2022 - December 2024 (31 months)
- **Validation**: 80/20 train-test split with stratified sampling
- **Hyperparameters**: Bayesian optimization (Optuna, 20 trials) minimizing validation MAE
- **Geographic coverage**: Arid, Temperate, and Continental climate zones

### Does it work outside the United States?
The model was trained on U.S. data, but the physical mechanisms (thermal inertia, radiation dynamics) are universal. Performance in other regions depends on:
- Availability of ERA5 data (global coverage)
- Climate similarity to training data
- Sensor installation conditions

We recommend validation against local reference stations before operational use.

### What are the limitations?
1. **Data latency**: ERA5 has ~5-day lag (use ERA5T or NWP for near-real-time)
2. **Site-specific bias**: Installation variations (mounting height, shading) cannot be fully corrected by population-level models
3. **Sensor platforms**: Validated only for PurpleAir PA-II sensors (other platforms may differ)
4. **Extreme conditions**: Limited validation data for extreme heat (>45°C) or cold (<-20°C)

### How does it compare to other calibration methods?
| Method | MAE (°C) | Data Requirements | Complexity |
|--------|----------|-------------------|------------|
| **Temporal-TempStrat (ours)** | 0.38-0.53 | 6h history + ERA5 | Medium |
| Temporal-National (ours) | 0.77 | 6h history + ERA5 | Low |
| Linear regression | ~2.5 | Colocation data | Very low |
| Random Forest | ~1.2 | Colocation data | Medium |
| Neural networks | ~1.0 | Large colocation dataset | High |
| **Uncalibrated** | 5.4 ± 6.7 | None | N/A |

---

## Technical Questions

### What machine learning algorithm is used?
**XGBoost** (gradient boosted decision trees) with Bayesian hyperparameter optimization. We also tested CatBoost and LightGBM, which showed similar performance.

### Can I train my own model?
Yes! We provide complete training scripts:
```bash
python models/train_xgboost.py \
  --data data/processed/training_data.csv \
  --output results/models/my_model \
  --n-trials 20
```

See `docs/USAGE.md` for detailed instructions.

### What features are most important?
Based on SHAP analysis:
1. **Thermal memory** (lagged temperatures, moving averages): 54-69%
2. **Radiation** (solar, thermal, cumulative): 3-11% (higher in hot conditions)
3. **Geography** (lat/lon/elevation): 13-15%
4. **Humidity** (dewpoint, VPD): 3-4%

See Figure 5 in the paper for detailed feature importance breakdown.

### Why temperature stratification instead of climate zones?
Temperature stratification outperforms climate-zone stratification because:
- **Physical basis**: Sensor bias is driven by thermal conditions, not geography
- **Adaptability**: Same sensor experiences different strata across seasons
- **Homogeneity**: Reduces within-group variance (e.g., Arid zone spans -20 to 40°C)
- **Performance**: 32-51% better than climate-zone models

### How much memory/storage do the models require?
- **Model size**: ~45 MB per stratum (135 MB total for 3 strata)
- **Runtime memory**: ~100 MB during inference
- **Prediction latency**: <5 ms per sample
- **GPU**: Not required (CPU-only is sufficient)

### Can I deploy this on edge devices (Raspberry Pi, Arduino)?
Yes, with optimization:
- Use ONNX format for smaller model size
- Implement spatial-only models (no historical data storage)
- Consider quantization for reduced memory footprint

See `docs/DEPLOYMENT.md` (coming soon) for edge deployment guides.

---

## Web Interface

### How do I use the web interface?
1. Visit: https://huggingface.co/spaces/yunqianz/purpleair-calibration
2. Upload your CSV file (must include required columns)
3. Select calibration model (Temporal-TempStrat or Temporal-National)
4. Download calibrated results

No programming required!

### What format should my CSV file be?
Required columns:
- `timestamp`: Datetime (YYYY-MM-DD HH:MM:SS)
- `temperature`: Raw PurpleAir temperature (°C)
- `humidity`: Relative humidity (%)
- `latitude`, `longitude`, `elevation`: Sensor location
- ERA5 variables: `SSRD`, `STRD`, `SSHF`, `u10`, `v10`, `precipitation`

See `examples/sample_input.csv` for template.

### Is there a file size limit?
Yes, the web interface has a 50 MB upload limit. For larger datasets, use the Python package locally.

---

## Troubleshooting

### "Missing required columns" error
Ensure your DataFrame includes:
- `temperature`, `humidity`, `timestamp`
- ERA5 variables: `SSRD`, `STRD`, `SSHF`, `u10`, `v10`
- Sensor metadata: `latitude`, `longitude`, `elevation`

Run `data.columns` to check available columns.

### Models predict unrealistic temperatures
Possible causes:
1. **Units mismatch**: Ensure temperature is in °C, not °F
2. **Missing data**: Check for NaN values (`data.isnull().sum()`)
3. **Wrong time zone**: ERA5 uses UTC, ensure sensor data matches
4. **Feature engineering errors**: Verify temporal features computed correctly

### Poor performance on my sensor
Possible reasons:
1. **Installation issues**: Non-standard mounting affects bias patterns
2. **Geographic extrapolation**: Sensor in climate zone not well-represented in training data
3. **Sensor malfunction**: Hardware issues beyond calibration scope
4. **Data quality**: Errors in input features (ERA5 download issues, etc.)

Recommendation: Validate against nearby reference station if available.

### CDS API authentication fails
1. Register at: https://cds.climate.copernicus.eu/
2. Get API key from account page
3. Create `~/.cdsapirc` file:
   ```
   url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR_UID:YOUR_API_KEY
   ```
4. Test with: `python -c "import cdsapi; cdsapi.Client()"`

---

## Contributing and Support

### How can I contribute?
See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. Areas we welcome:
- Additional sensor platform support
- Real-time data integration
- Edge device optimization
- Documentation improvements

### Where can I get help?
- **GitHub Issues**: https://github.com/yourusername/purpleair-calibration/issues
- **Discussions**: https://github.com/yourusername/purpleair-calibration/discussions
- **Email**: lianglu@berkeley.edu

### Can I use this commercially?
Yes! This project is MIT licensed. You are free to use, modify, and distribute for commercial purposes. Please cite our paper if you use this work.

---

## Citation

If you use this calibration framework in your research, please cite:

```bibtex
@article{zhang2025purpleair,
  title={Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research},
  author={Zhang, Yunqian and Rong, Yan and Liang, Lu},
  journal={[Journal Name]},
  year={2025},
  doi={10.xxxx/xxxxxx}
}
```
