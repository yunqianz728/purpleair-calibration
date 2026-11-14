# Changelog

All notable user-facing changes are recorded here.

## [2.1.0] - 2026-11-14

### Added

- `paper/`: the evaluation behind the manuscript — model fitting across every
  configuration, the four deployment protocols, the reviewer analyses, and the
  figure code — with the outputs it produced under both tuning budgets. Each
  model record carries its metrics, its chosen hyperparameters and its full
  trial history.
- The paired training dataset, 797,744 hourly observations with all 63
  engineered features, attached to this release and documented in
  `data/README.md` with a checksum.
- `paper/data/download_era5.py`, which requests the two reanalysis products the
  features are built from exactly as the study used them.

### Changed

- Reported accuracy for the archived paper-configuration model is 0.78 °C MAE
  (RMSE 1.089, R² 0.9874), measured on the held-out 20% of the 797,744
  observations. The figure previously shown, 0.64 °C, came from an evaluation
  whose test rows were not held out from fitting throughout. The two models the
  application actually serves are unaffected and their published metrics were
  already correct.
- `data/` and the documentation now state that the reanalysis inputs are two
  products at two resolutions: ERA5-Land at 0.1° for radiation, sensible heat
  flux and precipitation, ERA5 single levels at 0.25° for the wind components.

### Fixed

- Analysis scripts no longer carry one machine's home directory in their
  defaults.

## [2.0.0] - 2026-08-31

### Added

- Public Streamlit calibration application with CSV mapping and validation.
- Exact 63-feature Temporal-National paper model.
- Separately validated sensor-only temporal and warm-up deployment models.
- Sensor-isolated lag and rolling feature engineering.
- Per-row model provenance and history status.
- Working example, interactive diagnostics, CSV export, and method report.
- Docker deployment for the public Hugging Face Space.
- GitHub Actions integration and Streamlit smoke tests.

### Changed

- Aligned all maintained documentation with the final national-model result.
- Separated pre-final temperature-stratified prototypes and historical project
  notes into labeled archival directories.
- Clarified workflow-specific validation metrics in the application.
- Changed sidebar behavior to Streamlit's responsive automatic mode.

### Fixed

- Prevented temporal features from crossing sensor or discontinuous-segment
  boundaries.
- Rejected incomplete ERA5 input in paper mode.
- Pinned the scikit-learn version used to load the XGBoost 2.1.4 models.

## [1.0.2] - 2026-02-05

- Historical pre-final deployment prototype.

[2.0.0]: https://github.com/yunqianz728/purpleair-calibration/releases/tag/v2.0.0
[1.0.2]: https://github.com/yunqianz728/purpleair-calibration/releases/tag/v1.0.2
