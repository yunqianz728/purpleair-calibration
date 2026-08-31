# Changelog

All notable user-facing changes are recorded here.

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
