# PurpleAir temperature calibration

[![Live app](https://img.shields.io/badge/Live_app-open-1769aa)](https://huggingface.co/spaces/yunqianz/purpleair-calibration)
[![Tests](https://github.com/yunqianz728/purpleair-calibration/actions/workflows/test.yml/badge.svg)](https://github.com/yunqianz728/purpleair-calibration/actions/workflows/test.yml)
[![Version](https://img.shields.io/badge/version-2.0.0-15548a.svg)](CHANGELOG.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18463819.svg)](https://doi.org/10.5281/zenodo.18463819)
[![License: MIT](https://img.shields.io/badge/License-MIT-167c8b.svg)](LICENSE)

Calibrate hourly PurpleAir temperature readings with models developed from
797,744 observations across 31 U.S. states. The repository accompanies:

> Zhang, Y., Rong, Y., & Liang, L. *Nationwide Evaluation and Calibration of
> PurpleAir Temperature Sensors for Urban Thermal Environment Research*.

The [public web app](https://huggingface.co/spaces/yunqianz/purpleair-calibration)
supports CSV upload, explicit column mapping, validation, interactive results,
model provenance for every row, and downloadable calibrated data.

## Study result

PurpleAir devices showed a mean warm bias of 5.4°C, reaching approximately
13.5°C during peak solar radiation. The final Temporal-National XGBoost model
achieved 0.64°C mean absolute error (MAE), 0.87°C root mean squared error
(RMSE), and R² = 0.992 on the held-out test set. A single national model
performed consistently across the evaluated temperature regimes and climate
zones.

## Two app workflows

| Workflow | Input | Held-out performance | Purpose |
|---|---|---:|---|
| Direct calibration | timestamp, temperature, humidity, latitude, longitude | Temporal: MAE 0.813°C; warm-up: MAE 1.149°C | Standard PurpleAir exports |
| Final paper model | Direct inputs + SSHF, SSRD, STRD, TP, u10, v10 from ERA5 | MAE 0.64°C; RMSE 0.87°C | Exact 63-feature Temporal-National model |

Direct calibration uses a 49-feature sensor-only temporal model after six
prior hourly readings. The first six hours and isolated readings use a
24-feature instant model. Both deployment models were fitted to the same study
training table and evaluated on a fixed 20% observation-level holdout. Every
downloaded row records which model produced its value.

## Use the web app

1. Open the [calibration app](https://huggingface.co/spaces/yunqianz/purpleair-calibration).
2. Download the included example CSV or upload your own file.
3. Map the five required columns and choose the temperature unit.
4. Run validation and calibration.
5. Inspect the chart, processing summary, and row-level provenance.
6. Download the calibrated CSV and method report.

Minimal CSV:

```csv
timestamp,temperature,humidity,latitude,longitude,sensor_id
2024-01-15 10:00:00,68.5,45.2,37.7749,-122.4194,example-001
2024-01-15 11:00:00,72.3,43.8,37.7749,-122.4194,example-001
```

Optional columns improve context: `elevation`, `tree_canopy_cover`, and `life`
(days since deployment). Files containing multiple devices should include
`sensor_id`; otherwise coordinates identify each time series.

## Run locally

```bash
git clone https://github.com/yunqianz728/purpleair-calibration.git
cd purpleair-calibration/app
python -m pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. Run the integration checks with:

```bash
python test_calibration.py
```

## Reproduce the deployment models

The web models can be regenerated from the manuscript's engineered training
table and fitted Temporal-National model:

```bash
cd app
python train_deployment_models.py \
  --data /path/to/training_data_with_classification.csv \
  --paper-model /path/to/Temporal-National-XGBoost.pkl \
  --output models
```

Model metadata, validation metrics, and sample sizes are stored in
[`app/models/model_metadata.json`](app/models/model_metadata.json).

## Repository map

```text
app/
  app.py                         Streamlit interface
  sample_data.csv                Working upload example
  test_calibration.py            Integration checks
  train_deployment_models.py     Reproducible model export
  models/                        Three deployed XGBoost models + metadata
  utils/feature_engineering.py   Sensor-isolated temporal features
  utils/model_predictor.py       Model selection and provenance
docs/                             Maintained usage and FAQ documentation
legacy/                           Superseded prototypes and release utilities
```

## Scope

- Study population: PA-II sensors across Arid, Temperate, and Continental U.S.
  climate zones.
- Study period: June 2022 through December 2024.
- Temporal grouping: readings from different sensors and discontinuous time
  segments are processed independently.
- Paper mode expects ERA5 variables in the units used by the archived study
  data.
- Calibrated values support research and screening. Operational heat warning
  systems should retain reference-grade measurements and established safety
  protocols.
- Timestamps should use local standard time to match study feature engineering.

## Data and software

- Code archive: [10.5281/zenodo.18463819](https://doi.org/10.5281/zenodo.18463819)
- ERA5 archive: [10.5281/zenodo.18485026](https://doi.org/10.5281/zenodo.18485026)
- PurpleAir data: <https://www2.purpleair.com/>
- HadISD reference data: <https://www.metoffice.gov.uk/hadobs/hadisd/>
- ERA5 source: <https://cds.climate.copernicus.eu/>

## Documentation and support

- [Usage guide](docs/USAGE.md)
- [Frequently asked questions](docs/FAQ.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Report a problem](https://github.com/yunqianz728/purpleair-calibration/issues)

Historical pre-final prototypes and deployment notes are retained under
[`legacy/`](legacy/README.md) and [`docs/archive/`](docs/archive/README.md) for
provenance. They are clearly separated from the maintained final workflow.

## Citation

GitHub can generate citation text from [`CITATION.cff`](CITATION.cff). For a
versioned software citation, use the archived code DOI
[10.5281/zenodo.18463819](https://doi.org/10.5281/zenodo.18463819).

## Authors and license

Yunqian Zhang, Yan Rong, and Lu Liang. Correspondence: lianglu@berkeley.edu.

Released under the [MIT License](LICENSE).
