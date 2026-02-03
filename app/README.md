# PurpleAir Temperature Calibration Web App

A user-friendly web interface for calibrating PurpleAir temperature sensor readings using machine learning.

## 🌟 Features

- **Zero Installation** - Run directly in your browser
- **Drag & Drop** - Upload CSV files with a simple interface
- **Real-Time Calibration** - Get results in seconds
- **Interactive Visualizations** - Compare original vs calibrated temperatures
- **Download Results** - Export calibrated data and reports
- **Mobile Friendly** - Works on phones, tablets, and desktops

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
timestamp,temperature,humidity
2024-01-01 00:00:00,75.2,45
2024-01-01 01:00:00,74.8,46
2024-01-01 02:00:00,73.5,48
```

**Required columns:**
- `timestamp` (or `time`, `date`) - Date/time of reading
- `temperature` (or `temp`) - Sensor temperature (°F or °C)

**Optional columns** (for better accuracy):
- `humidity` - Relative humidity (%)
- `latitude`, `longitude` - Sensor location
- `pm25` - PM2.5 concentration

### Step 2: Upload & Calibrate

1. Visit the web app
2. Drag and drop your CSV file
3. Select temperature unit (°F or °C)
4. Choose calibration model
5. Click "Start Calibration"

### Step 3: Download Results

- **Calibrated Data (CSV)** - Complete dataset with corrected temperatures
- **Summary Report (TXT)** - Statistics and methodology

## 🎯 Model Options

### High Accuracy (Temporal-TempStrat) ⭐ Recommended

- **MAE**: 0.38-0.53°C
- **Best for**: Research, policy analysis, health studies
- **Processing**: ~5 seconds per 1000 readings

### Fast (Temporal-National)

- **MAE**: 0.77°C
- **Best for**: Quick checks, real-time applications
- **Processing**: ~2 seconds per 1000 readings

### Spatial (Climate-Based)

- **MAE**: 0.93°C
- **Best for**: Geographic analysis
- **Processing**: ~3 seconds per 1000 readings

## 📈 Performance

- **90% error reduction** vs uncalibrated sensors
- Validated on **797,744 observations** from **31 U.S. states**
- Handles datasets from **100 to 100,000+ readings**

## 🔧 Customization

### Change Theme

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Add Custom Model

Replace the calibration logic in `app.py`:

```python
# Load your trained model
import joblib
model = joblib.load('your_model.pkl')

# Apply calibration
calibrated_temps = model.predict(features)
```

## 🆘 Troubleshooting

### "Column not found" error

- Ensure your CSV has `temperature` or `temp` column
- Check column names are spelled correctly

### "Upload failed" error

- File must be CSV format
- Maximum file size: 200 MB
- Check file is not corrupted

### Calibration takes too long

- Try the "Fast" model for large datasets
- Consider sampling your data if >100,000 readings

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
