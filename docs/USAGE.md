# Usage guide

## Use the public application

Open the [PurpleAir Temperature Calibration app](https://huggingface.co/spaces/yunqianz/purpleair-calibration).

1. Choose **Direct calibration** or **Final paper model**.
2. Download the known-good example or upload a CSV.
3. Map the required columns and select Fahrenheit or Celsius.
4. Review validation messages.
5. Run calibration.
6. Inspect the chart, processing summary, model labels, and history status.
7. Download the calibrated CSV and method report.

Uploads are limited to 100,000 rows per run.

## Direct calibration input

Required fields:

| Field | Description |
|---|---|
| `timestamp` | Hourly local-standard-time timestamp |
| `temperature` | PurpleAir enclosure temperature in the selected unit |
| `humidity` | Relative humidity, 0–100% |
| `latitude` | Sensor latitude |
| `longitude` | Sensor longitude |

Recommended fields:

- `sensor_id` for files containing multiple sensors;
- `elevation` in metres;
- `tree_canopy_cover`; and
- `life`, measured as days since deployment.

The direct workflow uses a sensor-only temporal model after six prior
continuous hourly readings and an instant warm-up model for earlier or isolated
records. Its held-out MAE is 0.813°C for full-history rows and 1.149°C for
warm-up rows.

Minimal example:

```csv
timestamp,temperature,humidity,latitude,longitude,sensor_id
2024-01-15 10:00:00,68.5,45.2,37.7749,-122.4194,example-001
2024-01-15 11:00:00,72.3,43.8,37.7749,-122.4194,example-001
```

## Final paper model input

Paper mode runs the exact 63-feature Temporal-National XGBoost model reported
in the final manuscript. It requires all direct fields plus complete values for:

- `sshf`: surface sensible heat flux;
- `ssrd`: surface solar radiation downwards;
- `strd`: surface thermal radiation downwards;
- `tp`: total precipitation;
- `u10`: 10-metre eastward wind; and
- `v10`: 10-metre northward wind.

The paper model achieved 0.78°C MAE, 1.09°C RMSE, and R² = 0.987 on the
held-out test set. Supply ERA5 variables in the units used by the archived
study table. Missing weather values produce a validation error.

## Output columns

The downloaded CSV retains the prepared input and adds:

| Column | Meaning |
|---|---|
| `temperature_calibrated` | Model estimate in the selected temperature unit |
| `calibration_correction` | Sensor temperature minus calibrated estimate |
| `model_used` | Exact model responsible for the row |
| `history_status` | Whether six prior hourly records were available |

The correction is an applied model adjustment. It is not an error estimate for
the uploaded observations.

## Run locally

```bash
git clone https://github.com/yunqianz728/purpleair-calibration.git
cd purpleair-calibration/app
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

Run the integration checks from the repository root:

```bash
python app/test_calibration.py
```

## Reproduce deployment models

The export script trains the two sensor-only deployment models from the
engineered study table and converts the fitted paper model to XGBoost's UBJ
format:

```bash
cd app
python train_deployment_models.py \
  --data /path/to/training_data_with_classification.csv \
  --paper-model /path/to/Temporal-National-XGBoost.pkl \
  --output models
```

Validation metrics and training metadata are stored in
`app/models/model_metadata.json`.

## Scope

- Study period: June 2022 through December 2024.
- Study population: PA-II sensors across 31 U.S. states.
- Evaluated climate zones: Arid, Temperate, and Continental.
- Timestamps: local standard time.
- Operational use: retain reference-grade observations for safety-critical
  decisions.

See the [FAQ](FAQ.md) for model selection, limits, privacy, and citation.
