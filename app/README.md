# PurpleAir Temperature Calibration Web App

A user-friendly web interface for calibrating PurpleAir temperature sensor readings using machine learning.

## 🌟 Features

- **Temperature-Stratified Models** - 3 specialized XGBoost models (Cold/Moderate/Hot)
- **Automatic ERA5 Integration** - Fetches meteorological data for your location/time
- **63 Engineered Features** - Temporal, spatial, and meteorological variables
- **Real-Time Calibration** - Get results in 10-30 seconds per 1000 records
- **Interactive Visualizations** - Compare original vs calibrated temperatures
- **Download Results** - Export calibrated data and detailed reports
- **Temperature Regime Analysis** - See which model was applied to each reading

## 🚀 Quick Start

### Option 1: Run Locally

```bash
# Navigate to app directory
cd app/

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Option 2: Deploy to Streamlit Cloud (Free!)

1. **Fork this repository** on GitHub

2. **Go to** [Streamlit Cloud](https://streamlit.io/cloud)

3. **Click** "New app"

4. **Select**:
   - Repository: `yunqianz728/purpleair-calibration`
   - Branch: `main`
   - Main file path: `app/app.py`

5. **Click** "Deploy"

Your app will be live at: `https://your-app-name.streamlit.app`

### Option 3: Deploy to Hugging Face Spaces

1. **Create a new Space** at [Hugging Face](https://huggingface.co/spaces)

2. **Select**:
   - SDK: Streamlit
   - Name: `purpleair-calibration`

3. **Upload files**:
   - `app.py`
   - `requirements.txt`

4. **Your app will be live** at: `https://huggingface.co/spaces/YOUR_USERNAME/purpleair-calibration`

## 📊 Usage

### Step 1: Prepare Your Data

Create a CSV file with PurpleAir sensor data:

```csv
timestamp,temperature,humidity,latitude,longitude
2024-01-15 10:00:00,68.5,45.2,37.7749,-122.4194
2024-01-15 11:00:00,72.3,43.8,37.7749,-122.4194
2024-01-15 12:00:00,75.1,41.5,37.7749,-122.4194
```

**Required columns:**
- `timestamp` (or `time`, `date`) - Date/time (YYYY-MM-DD HH:MM:SS)
- `temperature` (or `temp`) - Sensor temperature (°F or °C)
- `humidity` - Relative humidity (0-100%)
- `latitude` - Sensor latitude (-90 to 90)
- `longitude` - Sensor longitude (-180 to 180)

**Important Notes:**
- Timestamps must be between **2022-01-01** and **2024-12-31** (ERA5 data availability)
- Coordinates should be within **CONUS** (continental US) for best results
- **Hourly data** works best (model trained on hourly observations)
- See `sample_data.csv` for a complete example

### Step 2: Upload & Calibrate

1. Visit the web app
2. Drag and drop your CSV file
3. Select temperature unit (°F or °C)
4. Choose calibration model
5. Click "Start Calibration"

### Step 3: Download Results

- **Calibrated Data (CSV)** - Complete dataset with corrected temperatures
- **Summary Report (TXT)** - Statistics and methodology

## 🎯 Calibration Model

### Temporal-TempStrat (Active)

Temperature-stratified machine learning calibration using **3 specialized XGBoost models**:

- **Cold Model** (<10°C): RMSE 1.52°C, 25 MB
- **Moderate Model** (10-30°C): RMSE 1.38°C, 9.4 MB
- **Hot Model** (>30°C): RMSE 1.45°C, 9.6 MB

**Overall Performance**: RMSE 1.43°C

**Why Temperature Stratification?**
- Sensor bias varies significantly across temperature ranges
- Cold regime: Minimal solar heating, conduction-dominated errors
- Moderate regime: Balanced thermal conditions
- Hot regime: Strong solar heating effects, radiation-dominated errors

**Processing Pipeline:**
1. **Data Preparation** - Standardize column names, convert units
2. **ERA5 Data Fetching** - Retrieve meteorological data for each location/time
3. **Feature Engineering** - Calculate 63 features (temporal, spatial, meteorological)
4. **Model Application** - Apply appropriate model based on temperature regime

**Processing Time**: ~10-30 seconds per 1000 records (depends on ERA5 data access)

## 📈 Performance

- **RMSE: 1.43°C overall** (compared to ASOS/AWOS reference stations)
- **70-85% error reduction** vs uncalibrated sensors (RMSE ~5-8°C)
- Validated on **2,682 sensors** across **CONUS** (2018-2022)
- Handles datasets from **10 to 100,000+ readings**

**Performance by Temperature Range:**
- Cold (<10°C): RMSE 1.52°C
- Moderate (10-30°C): RMSE 1.38°C
- Hot (>30°C): RMSE 1.45°C

**Validation Strategy:**
- Training: 70% of sensor-hours (stratified by climate zone)
- Testing: 30% hold-out set (unseen sensors and time periods)
- Cross-validation: 5-fold stratified CV

## 🔧 Configuration

### ERA5 Data Path

Edit `utils/era5_reader.py` to change the ERA5 data directory:

```python
ERA5_DATA_DIR = "/path/to/your/era5/data"
```

**ERA5 file format**: `YYYY-MM.nc` (e.g., `2024-01.nc`)

**Required ERA5 variables**:
- `sshf`: Surface sensible heat flux
- `ssrd`: Surface solar radiation downwards
- `strd`: Surface thermal radiation downwards
- `tp`: Total precipitation
- `u10`, `v10`: Wind components at 10m

### Streamlit Theme

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### File Structure

```
app/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── sample_data.csv                 # Example input data
├── models/                         # Trained XGBoost models (44 MB)
│   ├── station_temperature_cold_xgboost.pkl
│   ├── station_temperature_normal_xgboost.pkl
│   └── station_temperature_hot_xgboost.pkl
└── utils/                          # Calibration modules
    ├── era5_reader.py              # ERA5 data loader
    ├── feature_engineering.py      # 63-feature calculator
    └── model_predictor.py          # Temperature-stratified calibration
```

## 🆘 Troubleshooting

### "ERA5 data file not found"

**Cause**: ERA5 NetCDF files missing or incorrectly named

**Solutions**:
- Verify ERA5 files exist in the data directory (`/Users/yunqianzhang/Desktop/PA/气象数据/`)
- Check file names match pattern: `YYYY-MM.nc` (e.g., `2024-01.nc`)
- Ensure your timestamps fall within 2022-01 to 2024-12
- Update `ERA5_DATA_DIR` in `utils/era5_reader.py` if using different path

### "Missing latitude or longitude values"

**Cause**: CSV has NaN or empty lat/lon values

**Solutions**:
- Ensure your CSV has `latitude` and `longitude` columns
- Check for NaN or empty values: `df.isna().sum()`
- Coordinates must be numeric (not strings)
- Latitude range: -90 to 90
- Longitude range: -180 to 180

### "Column not found" error

**Solutions**:
- Ensure your CSV has required columns: `timestamp`, `temperature`, `humidity`, `latitude`, `longitude`
- Check column names are spelled correctly (case-insensitive)
- Use column name detection in Step 2 to verify

### Calibration takes too long

**Causes**: Large datasets or slow ERA5 data access

**Solutions**:
- Normal: ~30 seconds for 1000 records
- Large files (>10,000 rows) may take several minutes
- ERA5 data access is the main bottleneck
- Consider splitting very large datasets into smaller batches
- Ensure ERA5 files are on fast storage (SSD preferred)

### "Module not found" errors

**Solutions**:
- Run `pip install -r requirements.txt` again
- Verify Python version: `python --version` (must be 3.10+)
- Check that `utils/` directory exists and contains:
  - `era5_reader.py`
  - `feature_engineering.py`
  - `model_predictor.py`

### Performance Issues

**System Requirements**:
- Python 3.10+
- 2 GB RAM minimum (4 GB recommended for large datasets)
- ~50 GB disk space for ERA5 data

**Benchmarks** (MacBook Pro M1, 16 GB RAM):
- 100 records: ~5 seconds
- 1,000 records: ~30 seconds
- 10,000 records: ~5 minutes

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yunqianz728/purpleair-calibration/issues)
- **Email**: lianglu@berkeley.edu
- **Documentation**: [Main README](../README.md)

## 📄 Citation

If you use this tool in your research, please cite:

```bibtex
@software{zhang_2026_18463819,
  author       = {Zhang, Yunqian and Rong, Yan and Liang, Lu},
  title        = {PurpleAir Temperature Sensor Calibration},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.0.2},
  doi          = {10.5281/zenodo.18463819},
  url          = {https://doi.org/10.5281/zenodo.18463819}
}
```

## 📜 License

MIT License - See [LICENSE](../LICENSE) for details

---

**Built with** ❤️ **by** Yunqian Zhang & Lu Liang
**University of California, Berkeley**
