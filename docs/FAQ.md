# Frequently asked questions

## What does this project calibrate?

The software estimates ambient air temperature from the temperature and
humidity measurements recorded inside PurpleAir PA-II enclosures. These
measurements commonly show a warm bias caused by solar loading, internal heat,
and limited ventilation.

## Which workflow should I use?

The web app provides two explicitly labeled workflows:

| Workflow | Required input | Held-out performance | Recommended use |
|---|---|---:|---|
| Direct calibration | Timestamp, temperature, humidity, latitude, longitude | Temporal MAE 0.813°C; warm-up MAE 1.149°C | Standard PurpleAir exports |
| Final paper model | Direct inputs plus SSHF, SSRD, STRD, TP, u10, and v10 | MAE 0.64°C; RMSE 0.87°C; R² 0.992 | Exact manuscript model |

Direct calibration switches to its 49-feature temporal model after six prior
continuous hourly records. Earlier and isolated readings use a 24-feature
instant model. Every output row records the model used.

## Does direct calibration reproduce the paper result?

The 0.64°C paper result applies to the 63-feature Temporal-National model with
complete ERA5 inputs. Direct calibration uses separately trained sensor-only
deployment models and reports their own validation metrics.

## What timestamp should I provide?

Use local standard time to match the feature engineering in the study. Sort
records by sensor and time. Include `sensor_id` when a file contains more than
one device; otherwise coordinates define the time series.

## What units are accepted?

The app accepts Fahrenheit or Celsius sensor temperature and relative humidity
in percent. Paper mode expects ERA5 variables in the same units as the archived
study table. The interface validates required values and never substitutes zero
for missing ERA5 data.

## What happens during the first six hours?

Lagged and rolling features require prior hourly observations. Direct mode uses
the instant warm-up model until six prior records are available. Paper mode
still requires complete ERA5 inputs and identifies history status in the
download.

## Can I calibrate multiple sensors in one CSV?

Yes. Add a `sensor_id` column so that lags and rolling windows remain isolated
by device. Discontinuous hourly segments are also processed independently.

## How large can an upload be?

The public app accepts CSV files with up to 100,000 rows per run. Larger jobs
can use the same modules locally in batches.

## Does the model apply outside the United States?

The study evaluated PA-II sensors across Arid, Temperate, and Continental U.S.
climate zones from June 2022 through December 2024. Use in other regions,
sensor platforms, or installation configurations requires independent local
validation.

## Can I use the output for heat warnings?

The calibrated values support research and screening. Safety-critical heat
warning systems should retain reference-grade observations and established
operational protocols.

## Are uploaded files retained?

The application processes an upload in the active session and does not include
application code that stores uploaded CSV files.

## How should I cite the software?

Use the repository's `CITATION.cff` metadata and the archived code DOI:
[10.5281/zenodo.18463819](https://doi.org/10.5281/zenodo.18463819).

## Where can I get help?

Open an issue at
<https://github.com/yunqianz728/purpleair-calibration/issues> with a minimal,
de-identified example.
