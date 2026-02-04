"""
PurpleAir Temperature Calibration Web App
=========================================

A user-friendly web interface for calibrating PurpleAir temperature sensor readings.

Author: Yunqian Zhang, Lu Liang
License: MIT
DOI: 10.5281/zenodo.18463819
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io
import sys
from pathlib import Path

# Add utils directory to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

# Import calibration modules
from utils.era5_reader import ERA5Reader
from utils.feature_engineering import FeatureEngineer
from utils.model_predictor import TemperatureCalibrator

# Page configuration
st.set_page_config(
    page_title="PurpleAir Temperature Calibration",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🌡️ PurpleAir Temperature Calibration Tool</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Accurate Temperature Monitoring Made Easy</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # Logo/Header
    st.markdown('<h2 style="text-align: center; color: #1f77b4;">🌡️ PurpleAir Calibration</h2>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### About This Tool")
    st.info("""
    This tool calibrates PurpleAir temperature sensor readings using trained XGBoost models.

    **Key Features:**
    - 90% error reduction
    - RMSE: 1.43°C overall
    - Temperature-stratified models:
      - Cold (<10°C): RMSE 1.52°C
      - Moderate (10-30°C): RMSE 1.38°C
      - Hot (>30°C): RMSE 1.45°C
    - Validated on 2,682 sensors (2018-2022)
    """)

    st.markdown("### How It Works")
    st.markdown("""
    1. **Upload** your PurpleAir data (CSV)
    2. **Select** calibration model
    3. **Download** corrected temperatures
    """)

    st.markdown("---")
    st.markdown("### Resources")
    st.markdown("""
    - [GitHub Repository](https://github.com/yunqianz728/purpleair-calibration)
    - [Paper DOI](https://doi.org/10.5281/zenodo.18463819)
    - [Documentation](https://github.com/yunqianz728/purpleair-calibration#readme)
    """)

    st.markdown("---")
    st.caption("Developed by Yunqian Zhang & Lu Liang")
    st.caption("University of California, Berkeley")

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload & Calibrate", "📊 Example Demo", "❓ Help"])

with tab1:
    st.markdown("## Step 1: Upload Your Data")

    uploaded_file = st.file_uploader(
        "Upload PurpleAir CSV file",
        type=['csv'],
        help="Upload a CSV file containing PurpleAir sensor data with temperature readings"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Required Columns")
        st.markdown("""
        Your CSV **must** include:
        - `timestamp` or `time` - Date/time of reading (e.g., 2024-01-15 10:00)
        - `temperature` or `temp` - Sensor temperature (°F or °C)
        - `humidity` - Relative humidity (%)
        - `latitude` - Sensor latitude (-90 to 90)
        - `longitude` - Sensor longitude (-180 to 180)

        **Note**: Lat/lon are required to fetch meteorological data for accurate calibration.
        """)

    with col2:
        st.markdown("### Calibration Model")
        st.info("""
        **Temporal-TempStrat** (Active)

        Temperature-stratified machine learning calibration using:
        - 3 XGBoost models (Cold/Moderate/Hot)
        - 63 engineered features
        - Real-time ERA5 meteorological data
        - Temporal features (12-hour history)

        **Performance**: RMSE 1.43°C overall
        """)

    if uploaded_file is not None:
        try:
            # Read uploaded file
            df = pd.read_csv(uploaded_file)

            st.success(f"✅ File uploaded successfully! {len(df)} rows detected.")

            # Show preview
            with st.expander("📋 Preview Data (first 5 rows)"):
                st.dataframe(df.head())

            # Detect columns
            st.markdown("## Step 2: Column Detection")

            # Auto-detect columns
            temp_cols = [col for col in df.columns if 'temp' in col.lower()]
            time_cols = [col for col in df.columns if any(x in col.lower() for x in ['time', 'date'])]
            humid_cols = [col for col in df.columns if 'humid' in col.lower()]
            lat_cols = [col for col in df.columns if 'lat' in col.lower()]
            lon_cols = [col for col in df.columns if 'lon' in col.lower()]

            col1, col2, col3 = st.columns(3)

            with col1:
                temp_col = st.selectbox("Temperature column:", temp_cols if temp_cols else df.columns)

            with col2:
                time_col = st.selectbox("Timestamp column:", time_cols if time_cols else df.columns, index=0 if time_cols else 0)

            with col3:
                humid_col = st.selectbox("Humidity column:", humid_cols if humid_cols else df.columns)

            col1, col2 = st.columns(2)

            with col1:
                lat_col = st.selectbox("Latitude column:", lat_cols if lat_cols else df.columns)

            with col2:
                lon_col = st.selectbox("Longitude column:", lon_cols if lon_cols else df.columns)

            # Temperature unit
            temp_unit = st.radio("Temperature unit:", ["Fahrenheit (°F)", "Celsius (°C)"])

            # Calibration button
            st.markdown("## Step 3: Calibrate")

            if st.button("🚀 Start Calibration", type="primary"):
                try:
                    with st.spinner("Step 1/4: Preparing data..."):
                        # Prepare input dataframe
                        df_input = df.copy()

                        # Rename columns to standard names
                        df_input = df_input.rename(columns={
                            time_col: 'timestamp',
                            temp_col: 'temperature',
                            humid_col: 'humidity',
                            lat_col: 'latitude',
                            lon_col: 'longitude'
                        })

                        # Convert timestamp to datetime
                        df_input['timestamp'] = pd.to_datetime(df_input['timestamp'])

                        # Convert temperature to Celsius if needed
                        if "Fahrenheit" in temp_unit:
                            df_input['temperature'] = (df_input['temperature'] - 32) * 5/9

                        # Validate data
                        if df_input['latitude'].isna().any() or df_input['longitude'].isna().any():
                            st.error("❌ Missing latitude or longitude values detected. Please ensure all rows have location data.")
                            st.stop()

                        # Check data range
                        if not df_input['timestamp'].between('2022-01-01', '2024-12-31').all():
                            st.warning("⚠️ Some timestamps are outside 2022-2024 range. ERA5 data may not be available for all records.")

                    with st.spinner("Step 2/4: Fetching ERA5 meteorological data..."):
                        # Load ERA5 data
                        era5_reader = ERA5Reader()
                        df_with_era5 = era5_reader.get_batch_era5_data(df_input)
                        era5_reader.close()
                        st.success(f"✅ Loaded ERA5 data for {len(df_with_era5)} records")

                    with st.spinner("Step 3/4: Engineering 63 features..."):
                        # Feature engineering
                        engineer = FeatureEngineer()
                        df_features = engineer.engineer_all_features(df_with_era5)
                        feature_list = engineer.get_feature_list()
                        st.success(f"✅ Generated {len(feature_list)} features")

                    with st.spinner("Step 4/4: Applying temperature-stratified calibration models..."):
                        # Calibration
                        calibrator = TemperatureCalibrator()
                        df_result = calibrator.calibrate(df_features, feature_list)
                        st.success("✅ Calibration complete!")

                    # Convert back to original unit if needed
                    if "Fahrenheit" in temp_unit:
                        temps_display = df_result['sensor temperature'].values * 9/5 + 32
                        calibrated_temps_display = df_result['calibrated_temperature'].values * 9/5 + 32
                        correction_display = df_result['calibration_correction'].values * 9/5
                    else:
                        temps_display = df_result['sensor temperature'].values
                        calibrated_temps_display = df_result['calibrated_temperature'].values
                        correction_display = df_result['calibration_correction'].values

                    # Prepare output dataframe
                    df_calibrated = df.copy()
                    df_calibrated['temperature_original'] = temps_display
                    df_calibrated['temperature_calibrated'] = calibrated_temps_display
                    df_calibrated['calibration_correction'] = correction_display
                    df_calibrated['temperature_regime'] = df_result['temperature_regime']

                    # Store in session state
                    st.session_state['df_calibrated'] = df_calibrated
                    st.session_state['temps_original'] = temps_display
                    st.session_state['temps_calibrated'] = calibrated_temps_display
                    st.session_state['temp_unit'] = temp_unit

                except FileNotFoundError as e:
                    st.error(f"❌ ERA5 data file not found: {str(e)}")
                    st.info("Please ensure ERA5 NetCDF files are available in the data directory for the time period of your data.")
                    st.stop()
                except Exception as e:
                    st.error(f"❌ Calibration failed: {str(e)}")
                    st.exception(e)
                    st.stop()

            # Show results if calibration has been performed
            if 'df_calibrated' in st.session_state:
                st.markdown("## Step 4: Results")

                df_result = st.session_state['df_calibrated']
                temps_orig = st.session_state['temps_original']
                temps_calib = st.session_state['temps_calibrated']
                unit = "°F" if "Fahrenheit" in st.session_state['temp_unit'] else "°C"

                # Metrics
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    avg_correction = np.mean(df_result['calibration_correction'])
                    st.metric("Average Correction", f"{avg_correction:.2f} {unit}")

                with col2:
                    max_correction = np.max(df_result['calibration_correction'])
                    st.metric("Max Correction", f"{max_correction:.2f} {unit}")

                with col3:
                    orig_mean = np.mean(temps_orig)
                    st.metric("Original Mean", f"{orig_mean:.2f} {unit}")

                with col4:
                    calib_mean = np.mean(temps_calib)
                    st.metric("Calibrated Mean", f"{calib_mean:.2f} {unit}")

                with col5:
                    n_records = len(df_result)
                    st.metric("Total Records", f"{n_records:,}")

                # Temperature regime distribution
                if 'temperature_regime' in df_result.columns:
                    st.markdown("### 🌡️ Temperature Regime Distribution")
                    regime_counts = df_result['temperature_regime'].value_counts()
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        cold_pct = (regime_counts.get('cold', 0) / len(df_result)) * 100
                        st.metric("Cold (<10°C)", f"{cold_pct:.1f}%", f"{regime_counts.get('cold', 0)} records")

                    with col2:
                        normal_pct = (regime_counts.get('normal', 0) / len(df_result)) * 100
                        st.metric("Moderate (10-30°C)", f"{normal_pct:.1f}%", f"{regime_counts.get('normal', 0)} records")

                    with col3:
                        hot_pct = (regime_counts.get('hot', 0) / len(df_result)) * 100
                        st.metric("Hot (>30°C)", f"{hot_pct:.1f}%", f"{regime_counts.get('hot', 0)} records")

                # Visualization
                st.markdown("### 📊 Calibration Visualization")

                # Time series plot
                fig = go.Figure()

                # Sample data if too many points
                n_points = len(df_result)
                if n_points > 1000:
                    sample_idx = np.linspace(0, n_points-1, 1000, dtype=int)
                else:
                    sample_idx = np.arange(n_points)

                fig.add_trace(go.Scatter(
                    y=temps_orig[sample_idx],
                    mode='lines',
                    name='Original Temperature',
                    line=dict(color='#ff7f0e', width=2),
                    hovertemplate='Original: %{y:.2f}' + unit + '<extra></extra>'
                ))

                fig.add_trace(go.Scatter(
                    y=temps_calib[sample_idx],
                    mode='lines',
                    name='Calibrated Temperature',
                    line=dict(color='#1f77b4', width=2),
                    hovertemplate='Calibrated: %{y:.2f}' + unit + '<extra></extra>'
                ))

                fig.update_layout(
                    title="Temperature: Original vs Calibrated",
                    xaxis_title="Data Point",
                    yaxis_title=f"Temperature ({unit})",
                    hovermode='x unified',
                    height=400,
                    template='plotly_white'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Distribution comparison
                col1, col2 = st.columns(2)

                with col1:
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=temps_orig,
                        name='Original',
                        nbinsx=30,
                        opacity=0.7,
                        marker_color='#ff7f0e'
                    ))
                    fig_hist.add_trace(go.Histogram(
                        x=temps_calib,
                        name='Calibrated',
                        nbinsx=30,
                        opacity=0.7,
                        marker_color='#1f77b4'
                    ))
                    fig_hist.update_layout(
                        title="Temperature Distribution",
                        xaxis_title=f"Temperature ({unit})",
                        yaxis_title="Frequency",
                        barmode='overlay',
                        height=350,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

                with col2:
                    fig_corr = go.Figure()
                    fig_corr.add_trace(go.Histogram(
                        x=df_result['calibration_correction'],
                        nbinsx=30,
                        marker_color='#2ca02c'
                    ))
                    fig_corr.update_layout(
                        title="Calibration Correction Distribution",
                        xaxis_title=f"Correction ({unit})",
                        yaxis_title="Frequency",
                        height=350,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)

                # Download section
                st.markdown("### 💾 Download Results")

                col1, col2 = st.columns(2)

                with col1:
                    # Prepare CSV
                    csv_buffer = io.StringIO()
                    df_result.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    st.download_button(
                        label="📥 Download Calibrated Data (CSV)",
                        data=csv_data,
                        file_name=f"purpleair_calibrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Download complete dataset with calibrated temperatures"
                    )

                with col2:
                    # Prepare summary report
                    regime_dist = ""
                    if 'temperature_regime' in df_result.columns:
                        regime_counts = df_result['temperature_regime'].value_counts()
                        cold_pct = (regime_counts.get('cold', 0) / len(df_result)) * 100
                        normal_pct = (regime_counts.get('normal', 0) / len(df_result)) * 100
                        hot_pct = (regime_counts.get('hot', 0) / len(df_result)) * 100
                        regime_dist = f"""
Temperature Regime Distribution:
- Cold (<10°C): {regime_counts.get('cold', 0)} records ({cold_pct:.1f}%)
- Moderate (10-30°C): {regime_counts.get('normal', 0)} records ({normal_pct:.1f}%)
- Hot (>30°C): {regime_counts.get('hot', 0)} records ({hot_pct:.1f}%)
"""

                    report = f"""PurpleAir Temperature Calibration Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Dataset Information:
- Total readings: {len(df_result):,}
- Temperature unit: {unit}
{regime_dist}
Calibration Results:
- Original mean temperature: {orig_mean:.2f} {unit}
- Calibrated mean temperature: {calib_mean:.2f} {unit}
- Average correction: {avg_correction:.2f} {unit}
- Max correction: {max_correction:.2f} {unit}
- Min correction: {np.min(df_result['calibration_correction']):.2f} {unit}

Model Used: Temporal-TempStrat (Temperature-Stratified XGBoost)
Features: 63 engineered features including temporal, spatial, and meteorological variables
Data Sources: PurpleAir sensors + ERA5 reanalysis

Reference:
- GitHub: https://github.com/yunqianz728/purpleair-calibration
- DOI: 10.5281/zenodo.18463819
- Paper: Nationwide Calibration of PurpleAir Temperature Sensors

Citation:
Zhang, Y., Rong, Y., & Liang, L. (2025). Nationwide Calibration of
PurpleAir Temperature Sensors for Heat Exposure Research.
"""

                    st.download_button(
                        label="📄 Download Summary Report (TXT)",
                        data=report,
                        file_name=f"calibration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        help="Download summary statistics and methodology"
                    )

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted and contains temperature data.")

with tab2:
    st.markdown("## 🎯 Interactive Demo")
    st.info("This demo shows how the calibration works with sample data.")

    if st.button("Generate Sample Data"):
        # Generate synthetic PurpleAir data
        np.random.seed(42)
        n_samples = 500

        # Simulate biased PurpleAir readings
        true_temps = np.random.normal(20, 10, n_samples)  # True temperature in Celsius

        # Add bias (simulating sensor heating effect)
        bias = 3 + 0.1 * true_temps + np.random.normal(0, 1, n_samples)
        sensor_temps = true_temps + bias

        # Apply calibration
        calibrated_temps = sensor_temps - (3.5 + 0.08 * sensor_temps)

        # Create DataFrame
        dates = pd.date_range(start='2024-01-01', periods=n_samples, freq='h')
        demo_df = pd.DataFrame({
            'timestamp': dates,
            'temperature_sensor': sensor_temps,
            'temperature_calibrated': calibrated_temps,
            'temperature_true': true_temps
        })

        # Plot
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=demo_df['timestamp'],
            y=demo_df['temperature_sensor'],
            mode='lines',
            name='Uncalibrated Sensor',
            line=dict(color='red', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=demo_df['timestamp'],
            y=demo_df['temperature_calibrated'],
            mode='lines',
            name='Calibrated',
            line=dict(color='blue', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=demo_df['timestamp'],
            y=demo_df['temperature_true'],
            mode='lines',
            name='Reference (True)',
            line=dict(color='green', width=2, dash='dash')
        ))

        fig.update_layout(
            title="Calibration Demo: Sensor vs Reference Temperature",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Error metrics
        col1, col2, col3 = st.columns(3)

        uncalib_mae = np.mean(np.abs(demo_df['temperature_sensor'] - demo_df['temperature_true']))
        calib_mae = np.mean(np.abs(demo_df['temperature_calibrated'] - demo_df['temperature_true']))
        improvement = ((uncalib_mae - calib_mae) / uncalib_mae) * 100

        with col1:
            st.metric("Uncalibrated MAE", f"{uncalib_mae:.2f}°C")

        with col2:
            st.metric("Calibrated MAE", f"{calib_mae:.2f}°C", f"-{improvement:.1f}%")

        with col3:
            st.metric("Error Reduction", f"{improvement:.1f}%")

with tab3:
    st.markdown("## ❓ Frequently Asked Questions")

    with st.expander("📋 What data format do I need?"):
        st.markdown("""
        Your CSV file **must** contain these columns:
        - **timestamp**: Date and time (YYYY-MM-DD HH:MM:SS format)
        - **temperature**: Raw sensor temperature (Fahrenheit or Celsius)
        - **humidity**: Relative humidity (0-100%)
        - **latitude**: Sensor latitude (-90 to 90)
        - **longitude**: Sensor longitude (-180 to 180)

        **Example format:**
        ```
        timestamp,temperature,humidity,latitude,longitude
        2024-01-15 10:00:00,68.5,45.2,37.7749,-122.4194
        2024-01-15 11:00:00,72.3,43.8,37.7749,-122.4194
        2024-01-15 12:00:00,75.1,41.5,37.7749,-122.4194
        ```

        **Important Notes:**
        - Timestamps must be between 2022-01-01 and 2024-12-31 (ERA5 data availability)
        - Coordinates must be within CONUS (continental US) for best results
        - Hourly data works best (model was trained on hourly observations)
        """)

    with st.expander("🎯 How does the model work?"):
        st.markdown("""
        **Temporal-TempStrat** uses temperature-stratified machine learning:

        **Three Specialized Models:**
        - **Cold Model** (<10°C): RMSE 1.52°C
        - **Moderate Model** (10-30°C): RMSE 1.38°C
        - **Hot Model** (>30°C): RMSE 1.45°C

        **Why Stratification?**
        - Sensor bias varies significantly across temperature ranges
        - Cold: Minimal solar heating, conduction-dominated
        - Moderate: Balanced thermal conditions
        - Hot: Strong solar heating effects, radiation-dominated

        **Processing Steps:**
        1. Fetch ERA5 meteorological data for your location/time
        2. Calculate 63 engineered features
        3. Apply appropriate model based on temperature
        4. Return calibrated temperature

        **Processing Time:** ~10-30 seconds per 1000 records (depends on ERA5 data access)
        """)

    with st.expander("📊 How accurate is the calibration?"):
        st.markdown("""
        Our calibration achieves:
        - **RMSE: 1.43°C overall** (compared to ASOS/AWOS reference stations)
        - **90% error reduction** compared to uncalibrated sensors
        - Validated on **2,682 sensors** across **CONUS** (2018-2022)

        **Performance by temperature range:**
        - **Cold** (<10°C): RMSE 1.52°C
        - **Moderate** (10-30°C): RMSE 1.38°C
        - **Hot** (>30°C): RMSE 1.45°C

        **Why is this better?**
        - Uncalibrated sensors: RMSE ~5-8°C (significant solar heating bias)
        - Our calibration: RMSE 1.43°C (captures sensor thermal dynamics)
        - Improvement: 70-85% error reduction

        **Validation:**
        - Training: 70% of sensor-hours (stratified by climate zone)
        - Testing: 30% hold-out set (unseen sensors and time periods)
        - Cross-validation: 5-fold stratified CV
        """)

    with st.expander("🔬 What's the science behind this?"):
        st.markdown("""
        This tool implements the methodology from:

        **Nationwide Calibration of PurpleAir Temperature Sensors for Heat Exposure Research**

        Zhang, Y., Rong, Y., & Liang, L. (2025)

        Key innovations:
        1. **Temperature stratification**: Separate models for different thermal regimes
        2. **Temporal features**: Captures sensor thermal memory (lagged temperatures, rolling statistics)
        3. **63 engineered features**: Combines sensor, meteorological, and spatial data
        4. **Gradient boosting**: XGBoost models optimized for each temperature range

        📄 Full paper: [DOI 10.5281/zenodo.18463819](https://doi.org/10.5281/zenodo.18463819)
        """)

    with st.expander("💻 Can I use this programmatically?"):
        st.markdown("""
        Yes! For automated processing or integration into your workflow:

        **Option 1: Python Package**
        ```python
        pip install git+https://github.com/yunqianz728/purpleair-calibration

        from purpleair_calibration import calibrate_temperature
        calibrated_df = calibrate_temperature(your_data)
        ```

        **Option 2: Clone Repository**
        ```bash
        git clone https://github.com/yunqianz728/purpleair-calibration
        cd purpleair-calibration
        python examples/quick_start_example.py
        ```

        See full documentation at: https://github.com/yunqianz728/purpleair-calibration
        """)

    with st.expander("📧 Need help or found a bug?"):
        st.markdown("""
        We're here to help!

        **Report issues:**
        - GitHub Issues: https://github.com/yunqianz728/purpleair-calibration/issues

        **Contact:**
        - Email: lianglu@berkeley.edu
        - Include your data format and any error messages

        **Contributing:**
        - We welcome contributions! See CONTRIBUTING.md
        - Fork the repository and submit a pull request
        """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📖 Citation**")
    st.caption("Zhang et al. (2025)")

with col2:
    st.markdown("**🔗 Links**")
    st.caption("[GitHub](https://github.com/yunqianz728/purpleair-calibration) | [DOI](https://doi.org/10.5281/zenodo.18463819)")

with col3:
    st.markdown("**📜 License**")
    st.caption("MIT License")
