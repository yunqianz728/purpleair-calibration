---
title: PurpleAir Temperature Calibration
emoji: 🌡️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: true
license: mit
tags:
  - temperature
  - calibration
  - xgboost
  - climate
  - sensors
  - environmental-science
---

# PurpleAir Temperature Calibration

Calibrate hourly PurpleAir temperature readings with models developed from
797,744 observations across 31 U.S. states.

The app provides:

- CSV upload with automatic column detection and explicit mapping
- Direct calibration from five standard PurpleAir fields
- Exact 63-feature Temporal-National paper model for ERA5-enriched data
- Sensor-isolated temporal feature engineering
- Row-level model provenance and history status
- Interactive checks, calibrated CSV export, and a method report

The final paper model achieved 0.78°C MAE, 1.09°C RMSE, and R² = 0.987 on the
held-out test set. Direct calibration uses separately validated sensor-only
models and displays their metrics in the Method & limits tab.

Source code: <https://github.com/yunqianz728/purpleair-calibration>

Code archive: <https://doi.org/10.5281/zenodo.18463819>
