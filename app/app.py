"""Public web application for PurpleAir temperature calibration."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.feature_engineering import ERA5_COLUMNS, FeatureEngineer
from utils.model_predictor import TemperatureCalibrator


APP_DIR = Path(__file__).resolve().parent
GITHUB_URL = "https://github.com/yunqianz728/purpleair-calibration"
ZENODO_CODE_URL = "https://doi.org/10.5281/zenodo.18463819"
ZENODO_ERA5_URL = "https://doi.org/10.5281/zenodo.18485026"
REQUIRED_NAMES = ("timestamp", "temperature", "humidity", "latitude", "longitude")

ALIASES = {
    "timestamp": ("timestamp", "time_stamp", "datetime", "date_time", "date created"),
    "temperature": (
        "temperature", "sensor temperature", "temp_f", "temp_c", "current_temp_f",
    ),
    "humidity": ("humidity", "relative_humidity", "rh", "current_humidity"),
    "latitude": ("latitude", "lat", "sensor_lat"),
    "longitude": ("longitude", "lon", "lng", "sensor_lon"),
    "sensor_id": ("sensor_id", "sensor index", "sensor_index", "id"),
    "elevation": ("elevation", "elevation_sensor", "altitude"),
    "tree_canopy_cover": ("tree_canopy_cover", "sensor_tcc", "tcc"),
    "life": ("life", "sensor_age", "age_days", "days_since_deployment"),
}


st.set_page_config(
    page_title="PurpleAir Temperature Calibration",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#132238; --muted:#5d6b7d; --blue:#1769aa; --cyan:#16a3b6; --paper:#f5f8fb; }
    .stApp { background: linear-gradient(180deg, #f7fbff 0, #ffffff 28rem); color: var(--ink); }
    .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem; }
    .hero { padding: 2.2rem 2.4rem; border: 1px solid #dce8f3; border-radius: 22px;
            background: radial-gradient(circle at 90% 10%, #d8f5f7, transparent 34%),
                        linear-gradient(135deg, #ffffff, #eff7ff); box-shadow: 0 18px 45px rgba(31,70,105,.08); }
    .eyebrow { color:#167c8b; font-size:.78rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
    .hero h1 { font-size: clamp(2.2rem, 5vw, 4.2rem); line-height:1.02; margin:.55rem 0 .85rem; color:#10233d; }
    .hero p { max-width:760px; font-size:1.08rem; line-height:1.65; color:#4e6176; }
    .pill { display:inline-block; margin:.75rem .45rem 0 0; padding:.36rem .72rem; border-radius:999px;
            background:#e7f3ff; color:#15548a; font-size:.82rem; font-weight:700; }
    .section-card { padding:1.25rem 1.35rem; border:1px solid #e0e9f1; border-radius:16px; background:#fff; }
    .micro { color:#66778a; font-size:.88rem; }
    [data-testid="stMetric"] { padding:1rem 1.1rem; border:1px solid #e1eaf2; border-radius:14px; background:#fff; }
    [data-testid="stFileUploader"] { border:1px dashed #83abc9; border-radius:16px; padding:.5rem; background:#f8fbfe; }
    .stButton > button, .stDownloadButton > button { border-radius:10px; font-weight:700; min-height:2.75rem; }
    .stTabs [data-baseweb="tab-list"] { gap:.5rem; }
    .stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0; padding:.65rem 1rem; }
    footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_calibrator() -> TemperatureCalibrator:
    return TemperatureCalibrator()


@st.cache_data
def sample_bytes() -> bytes:
    return (APP_DIR / "sample_data.csv").read_bytes()


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    raw = uploaded_file.getvalue()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("The CSV encoding could not be read. Save the file as UTF-8 and try again.")


def guess_column(columns, standard_name):
    normalized = {str(column).strip().lower(): column for column in columns}
    for alias in ALIASES[standard_name]:
        if alias in normalized:
            return normalized[alias]
    for column in columns:
        lower = str(column).lower()
        if any(alias in lower for alias in ALIASES[standard_name]):
            return column
    return None


def column_selector(label, standard_name, columns, required=True):
    detected = guess_column(columns, standard_name)
    options = list(columns) if required else ["— not provided —", *columns]
    if detected in options:
        index = options.index(detected)
    else:
        index = 0
    return st.selectbox(label, options, index=index, key=f"map_{standard_name}")


def validate_and_prepare(df, mapping, unit, mode):
    errors, warnings = [], []
    if len(df) == 0:
        errors.append("The file contains no data rows.")
    if len(df) > 100_000:
        errors.append("The public app accepts up to 100,000 rows per run.")
    required_selected = [mapping[name] for name in REQUIRED_NAMES]
    if len(set(required_selected)) != len(required_selected):
        errors.append("Each required field must map to a different CSV column.")

    standardized = df.copy()
    rename = {source: target for target, source in mapping.items() if source != "— not provided —"}
    standardized = standardized.rename(columns=rename)
    standardized["timestamp"] = pd.to_datetime(standardized["timestamp"], errors="coerce")
    for name in ("temperature", "humidity", "latitude", "longitude"):
        standardized[name] = pd.to_numeric(standardized[name], errors="coerce")
    for name in ("elevation", "tree_canopy_cover", "life", *ERA5_COLUMNS):
        if name in standardized:
            standardized[name] = pd.to_numeric(standardized[name], errors="coerce")

    missing_required = standardized[list(REQUIRED_NAMES)].isna().any(axis=1)
    if missing_required.any():
        errors.append(f"{int(missing_required.sum()):,} rows have invalid or missing required values.")
    if (~standardized["humidity"].dropna().between(0, 100)).any():
        errors.append("Humidity must be between 0 and 100 percent.")
    if (~standardized["latitude"].dropna().between(-90, 90)).any():
        errors.append("Latitude must be between -90 and 90 degrees.")
    if (~standardized["longitude"].dropna().between(-180, 180)).any():
        errors.append("Longitude must be between -180 and 180 degrees.")

    if unit == "Fahrenheit (°F)":
        standardized["temperature"] = (standardized["temperature"] - 32) * 5 / 9
    if (~standardized["temperature"].dropna().between(-60, 80)).any():
        warnings.append("Some converted temperatures fall outside −60 to 80°C. Confirm the selected unit.")

    key_columns = ["timestamp"]
    if "sensor_id" in standardized and standardized["sensor_id"].notna().any():
        key_columns.insert(0, "sensor_id")
    else:
        key_columns = ["latitude", "longitude", "timestamp"]
    duplicates = standardized.duplicated(key_columns, keep="first")
    if duplicates.any():
        warnings.append(f"{int(duplicates.sum()):,} duplicate sensor-time rows were removed.")
        standardized = standardized.loc[~duplicates].copy()

    if "sensor_id" not in standardized:
        warnings.append("Coordinates are being used to group readings. Add sensor_id when one file contains multiple devices.")
    for optional in ("elevation", "tree_canopy_cover", "life"):
        if optional not in standardized:
            warnings.append(f"{optional} is absent; XGBoost will use its learned missing-value path.")

    if mode == "paper":
        missing_weather = [name for name in ERA5_COLUMNS if name not in standardized]
        if missing_weather:
            errors.append("Paper mode requires these exact ERA5 columns: " + ", ".join(missing_weather))
        elif standardized[list(ERA5_COLUMNS)].isna().any().any():
            errors.append("Paper mode requires complete ERA5 values in every row.")

    return standardized, errors, warnings


def result_table(original, calibrated, unit):
    output = original.copy().reset_index(drop=True)
    celsius = calibrated["calibrated_temperature_c"].to_numpy()
    correction_c = calibrated["calibration_correction_c"].to_numpy()
    if unit == "Fahrenheit (°F)":
        output["temperature_calibrated"] = celsius * 9 / 5 + 32
        output["calibration_correction"] = correction_c * 9 / 5
    else:
        output["temperature_calibrated"] = celsius
        output["calibration_correction"] = correction_c
    output["model_used"] = calibrated["model_used"].to_numpy()
    output["history_status"] = calibrated["history_status"].to_numpy()
    return output


def calibration_report(output, mode, unit, metadata):
    unit_symbol = "°F" if "Fahrenheit" in unit else "°C"
    correction = output["calibration_correction"]
    lines = [
        "# PurpleAir temperature calibration report",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Mode: {'Temporal-National paper model' if mode == 'paper' else 'Adaptive sensor-only deployment models'}",
        f"Records: {len(output):,}",
        f"Temperature unit: {unit_symbol}",
        f"Mean applied correction: {correction.mean():.2f} {unit_symbol}",
        f"Median applied correction: {correction.median():.2f} {unit_symbol}",
        "",
        "The applied correction is a model output. It is not an error estimate for this uploaded dataset.",
        "Review the model scope and limitations before scientific or operational use.",
        "",
        f"Source code: {GITHUB_URL}",
        f"Code archive: {ZENODO_CODE_URL}",
        "",
        "## Model metadata",
        "",
    ]
    for name, details in metadata.items():
        if isinstance(details, dict) and "label" in details:
            lines.append(f"- {details['label']}: MAE {details.get('test_mae_c', '—')}°C; RMSE {details.get('test_rmse_c', '—')}°C")
    return "\n".join(lines) + "\n"


def render_results(output, mode, unit, metadata, prefix="result"):
    unit_symbol = "°F" if "Fahrenheit" in unit else "°C"
    original_column = "temperature"
    correction = output["calibration_correction"]
    cols = st.columns(4)
    cols[0].metric("Readings calibrated", f"{len(output):,}")
    cols[1].metric("Mean correction", f"{correction.mean():.2f} {unit_symbol}")
    cols[2].metric("Median correction", f"{correction.median():.2f} {unit_symbol}")
    temporal_share = (output["history_status"] != "warm-up").mean() * 100
    cols[3].metric("Full-history rows", f"{temporal_share:.1f}%")

    plot_df = output.copy()
    if len(plot_df) > 2_000:
        plot_df = plot_df.iloc[np.linspace(0, len(plot_df) - 1, 2_000, dtype=int)]
    x = pd.to_datetime(plot_df.get("timestamp"), errors="coerce")
    if x.isna().all():
        x = np.arange(len(plot_df))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=plot_df[original_column], name="Sensor", mode="lines", line=dict(color="#e07a3f", width=1.8)))
    fig.add_trace(go.Scatter(x=x, y=plot_df["temperature_calibrated"], name="Calibrated", mode="lines", line=dict(color="#1769aa", width=2.2)))
    fig.update_layout(
        height=410, margin=dict(l=20, r=20, t=40, b=20), template="plotly_white",
        title="Sensor and calibrated temperature", yaxis_title=f"Temperature ({unit_symbol})",
        hovermode="x unified", legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig, width="stretch")

    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown("#### Output preview")
        show_columns = [name for name in ("timestamp", "sensor_id", "temperature", "temperature_calibrated", "calibration_correction", "model_used", "history_status") if name in output]
        st.dataframe(output[show_columns].head(30), width="stretch", hide_index=True)
    with right:
        st.markdown("#### Processing summary")
        counts = output["model_used"].value_counts().rename_axis("Model").reset_index(name="Rows")
        st.dataframe(counts, width="stretch", hide_index=True)
        st.caption("A correction value describes the adjustment applied to a sensor reading. Validation error requires independent reference observations.")

    csv = output.to_csv(index=False).encode("utf-8-sig")
    report = calibration_report(output, mode, unit, metadata)
    download_left, download_right = st.columns(2)
    download_left.download_button(
        "Download calibrated CSV", csv,
        file_name=f"purpleair_calibrated_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv", width="stretch", key=f"{prefix}_csv",
    )
    download_right.download_button(
        "Download method report", report,
        file_name=f"purpleair_calibration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown", width="stretch", key=f"{prefix}_report",
    )


with st.sidebar:
    st.markdown("### PurpleAir calibration")
    st.caption("Open research software · Version 2.0")
    st.markdown("---")
    st.markdown("**Final study model**")
    st.metric("Held-out MAE", "0.64°C")
    st.caption("Temporal-National XGBoost · 63 features · R² 0.992")
    st.markdown("---")
    st.markdown(f"[GitHub repository]({GITHUB_URL})")
    st.markdown(f"[Archived code]({ZENODO_CODE_URL})")
    st.markdown(f"[ERA5 archive]({ZENODO_ERA5_URL})")
    st.markdown("---")
    st.caption("Yunqian Zhang · Yan Rong · Lu Liang")
    st.caption("MIT License")


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Open research tool · Nationwide calibration</div>
      <h1>Turn PurpleAir heat bias into research-ready temperature.</h1>
      <p>Upload hourly sensor readings, inspect every assumption, and export calibrated temperatures with a reproducible model record. The workflow follows the final nationwide study across 31 U.S. states.</p>
      <span class="pill">797,744 hourly observations</span>
      <span class="pill">98 PurpleAir sensors</span>
      <span class="pill">Single national XGBoost model</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
calibrate_tab, example_tab, method_tab = st.tabs(["Calibrate data", "Working example", "Method & limits"])

with calibrate_tab:
    st.markdown("## Calibrate your CSV")
    st.caption("Your file is processed in this session. The app does not retain uploaded data.")
    mode_label = st.radio(
        "Choose a workflow",
        ["Direct calibration · five required columns", "Final paper model · ERA5 columns required"],
        horizontal=True,
        help="Direct calibration uses deployment models trained from the same study dataset. Paper mode runs the exact 63-feature Temporal-National model.",
    )
    mode = "paper" if mode_label.startswith("Final") else "accessible"

    intro_left, intro_right = st.columns([1.7, 1])
    with intro_left:
        uploaded = st.file_uploader("Drop a CSV here", type="csv", help="Maximum 100,000 rows")
    with intro_right:
        st.markdown("##### Start from a known-good file")
        st.download_button(
            "Download example CSV", sample_bytes(), file_name="purpleair_example.csv",
            mime="text/csv", width="stretch",
        )
        st.caption("The example contains hourly Fahrenheit readings from one sensor.")

    if uploaded is not None:
        try:
            raw_df = read_uploaded_csv(uploaded)
        except Exception as exc:
            st.error(str(exc))
            st.stop()
        st.success(f"Loaded {len(raw_df):,} rows and {len(raw_df.columns)} columns.")
        with st.expander("Preview and map columns", expanded=True):
            st.dataframe(raw_df.head(10), width="stretch", hide_index=True)
            map_cols = st.columns(3)
            mapping = {}
            for index, name in enumerate(REQUIRED_NAMES):
                with map_cols[index % 3]:
                    mapping[name] = column_selector(name.replace("_", " ").title(), name, raw_df.columns)
            st.markdown("**Optional context**")
            optional_cols = st.columns(4)
            for index, name in enumerate(("sensor_id", "elevation", "tree_canopy_cover", "life")):
                with optional_cols[index]:
                    mapping[name] = column_selector(name.replace("_", " ").title(), name, raw_df.columns, required=False)
            unit = st.radio("Input temperature unit", ["Fahrenheit (°F)", "Celsius (°C)"], horizontal=True)

        if st.button("Validate and calibrate", type="primary", width="stretch"):
            prepared, errors, warnings = validate_and_prepare(raw_df, mapping, unit, mode)
            for warning in warnings:
                st.warning(warning)
            if errors:
                for error in errors:
                    st.error(error)
            else:
                with st.spinner("Engineering features and running XGBoost…"):
                    engineered = FeatureEngineer().engineer_all_features(prepared)
                    calibrator = load_calibrator()
                    calibrated = calibrator.calibrate(engineered, mode=mode)
                    output = result_table(prepared, calibrated, unit)
                    st.session_state["calibration_output"] = output
                    st.session_state["calibration_mode"] = mode
                    st.session_state["calibration_unit"] = unit
                st.success("Calibration completed with a traceable model label for every row.")

        if "calibration_output" in st.session_state:
            st.markdown("## Results")
            render_results(
                st.session_state["calibration_output"],
                st.session_state["calibration_mode"],
                st.session_state["calibration_unit"],
                load_calibrator().get_model_info(),
                prefix="upload",
            )

with example_tab:
    st.markdown("## Run the real pipeline on included data")
    st.write("This example uses the packaged XGBoost deployment models. It demonstrates file structure, temporal warm-up, charts, and downloads.")
    if st.button("Run working example", type="primary", key="run_example"):
        sample = pd.read_csv(APP_DIR / "sample_data.csv")
        sample["temperature"] = (sample["temperature"] - 32) * 5 / 9
        engineered = FeatureEngineer().engineer_all_features(sample)
        calibrated = load_calibrator().calibrate(engineered, mode="accessible")
        output = result_table(sample, calibrated, "Celsius (°C)")
        st.session_state["example_output"] = output
    if "example_output" in st.session_state:
        render_results(
            st.session_state["example_output"], "accessible", "Celsius (°C)",
            load_calibrator().get_model_info(), prefix="example",
        )

with method_tab:
    st.markdown("## What the tool implements")
    paper_col, direct_col = st.columns(2)
    with paper_col:
        st.markdown("### Final paper model")
        st.write("A single Temporal-National XGBoost model uses 63 sensor, site, ERA5, and temporal features. It achieved 0.64°C MAE, 0.87°C RMSE, and R² = 0.992 on the held-out test set reported in the final manuscript.")
        st.info("Use this mode when your table already contains SSHF, SSRD, STRD, TP, u10, and v10 from ERA5 in the same units used by the archive.")
    with direct_col:
        st.markdown("### Direct calibration")
        st.write("Two deployment models make the site usable from standard PurpleAir exports. Continuous sequences switch to the sensor-only temporal model after six prior hourly records. Isolated and early readings use the instant warm-up model.")
        st.info("These deployment models are validated separately and identified in every downloaded row.")

    metadata = load_calibrator().get_model_info()
    rows = []
    for key in ("paper", "sensor_temporal", "instant"):
        item = metadata.get(key, {})
        if item:
            rows.append({
                "Model": item.get("label", key), "Features": item.get("features"),
                "Held-out MAE (°C)": item.get("test_mae_c"),
                "Held-out RMSE (°C)": item.get("test_rmse_c"), "R²": item.get("test_r2"),
            })
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.markdown("### Scope and responsible use")
    st.markdown(
        """
        - The study covers PA-II sensors in Arid, Temperate, and Continental U.S. climate zones from June 2022 through December 2024.
        - Site installation, enclosure changes, firmware changes, unusual shading, and extreme microclimates can shift performance.
        - ERA5 has several days of latency. Paper-mode near-real-time deployment requires an operational meteorological substitute that has been validated against the training inputs.
        - Calibrated output supports research and screening. Safety-critical heat warnings should retain reference-grade observations and established operational protocols.
        - Uploaded timestamps should represent local standard time, matching the study feature engineering.
        """
    )
    st.markdown("### Citation")
    st.code(
        "Zhang, Y., Rong, Y., & Liang, L. Nationwide Evaluation and Calibration of "
        "PurpleAir Temperature Sensors for Urban Thermal Environment Research.",
        language=None,
    )

st.markdown("---")
st.caption("PurpleAir Temperature Calibration · Open source under the MIT License · Model outputs include provenance for every row")
