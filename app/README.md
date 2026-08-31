# Web application guide

The Streamlit application calibrates PurpleAir temperature CSV files and
exports row-level model provenance.

## Required columns

| Field | Accepted example | Validation |
|---|---|---|
| timestamp | `2024-01-15 10:00:00` | parseable local-standard timestamp |
| temperature | `68.5` | Fahrenheit or Celsius, selected in the app |
| humidity | `45.2` | 0–100% |
| latitude | `37.7749` | −90 to 90 |
| longitude | `-122.4194` | −180 to 180 |

Recommended optional fields are `sensor_id`, `elevation`,
`tree_canopy_cover`, and `life`. `sensor_id` keeps temporal histories separate
when a file contains multiple devices. Coordinates are used when it is absent.

Paper mode also requires complete `sshf`, `ssrd`, `strd`, `tp`, `u10`, and
`v10` columns from ERA5 in the same units as the study archive.

## Start locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Run integration checks:

```bash
python test_calibration.py
```

## Model behavior

- Direct calibration uses the 49-feature sensor-only temporal model after six
  prior hourly records.
- Warm-up and isolated rows use the 24-feature instant model.
- Paper mode uses the final 63-feature Temporal-National XGBoost model.
- Discontinuous segments and different sensors receive independent lag and
  rolling features.
- XGBoost's learned missing-value paths handle absent optional site fields.
- Every output row includes `model_used` and `history_status`.

Validation metrics are stored in `models/model_metadata.json` and displayed in
the app's Method & limits tab.

## Container deployment

The included Dockerfile serves Streamlit on port 7860, the default application
port for Hugging Face Docker Spaces.

```bash
docker build -t purpleair-calibration .
docker run --rm -p 7860:7860 purpleair-calibration
```
