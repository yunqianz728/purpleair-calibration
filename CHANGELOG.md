# Changelog

All notable user-facing changes are recorded here.

## [Unreleased]

### Added

- `paper/results_wide/algo_comparison/summary.json`: LightGBM and CatBoost
  re-fitted under the protocol and widened search of the main results, for the
  four unstratified configurations (SI Section S4). LightGBM comes within about
  2% of XGBoost in test MAE (0.615 against 0.602 C for the national model, and
  about 1% better in the other three); CatBoost stays 5-12% behind, also at
  depths 14 and 16. Full per-trial histories are produced by
  `algo_comparison.py`.
- `paper/analysis/pressure_test.py`: the sensor's own barometric pressure
  (daily means from the PurpleAir API, fetched with
  `fetch_rssi.py --field pressure --average 1440`) as an additional predictor.
  The raw reading leaves error on sensors withheld from training unchanged;
  the pressure anomaly (relative to the sensor's mean) lowers it by about 2%,
  also when only the previous day's value is used.
- `paper/analysis/impervious_test.py`: NLCD imperviousness at the sensor, and
  the sensor-station difference, as additional predictors; on sensors withheld
  from training they change the error by about 1% or less (+1.1% and -0.5%).
- `paper/analysis/no_reanalysis_test.py`: the national model without the 14
  ERA5 / ERA5-Land predictors, which are released about five days late. Forward
  error rises from 1.08 to 1.16 C (7.7%).
- `paper/analysis/longer_ensemble_test.py`: the national model with the round
  limit doubled to 40,000; test MAE falls by only 1.2% (0.594 against 0.601 C).
- `paper/analysis/urban_form_points.py`: building height and population (GHSL
  R2023A) and tree canopy (Meta / WRI canopy height map) at every sensor and
  station, read block by block over HTTP.
- `paper/analysis/iecc_check.py`: the dewpoint split of the temperate sensors
  against the 2021 IECC moisture regimes (PNNL county map, not redistributed);
  they agree for all 33 sensors.

- `paper/results_wide/`: every result the revised manuscript reports, from the
  widened XGBoost search (`PA_SEARCH=wide`, 50 trials per configuration). Test
  MAE fell in all 28 configurations, by 13.4% on average; the national model
  reaches 0.60 C (0.72 C in `results_50trials/`). The boosters are not
  included; each model's JSON record carries its metrics, hyperparameters and
  trial history.
- `paper/analysis/search_space_summary.py`: where the tuned models sit in the
  original and the widened search space. In the original space all 28 chose
  the greatest depth allowed and 21 ended within 10% of the round limit; in the
  widened space none reaches the depth limit.
- `paper/analysis/capacity_curves.py` and `make_figure_capacity.py`: validation
  error after every boosting round, up to 20,000, for the national model and
  the two stratified designs fitted with identical hyperparameters (SI Figure
  S2). The national model gains more from additional rounds, so the comparison
  between stratified and national models depends on the capacity the search
  allows.
- `paper/analysis/seed_robustness.py`: the final fits behind the paper's
  comparisons repeated under five random partitions and seeds. Under the
  widened search the national model's MAE stays within 0.596-0.601 C, and
  every comparison holds in all five; seed 42 reproduces Table 2 exactly.

### Changed

- `paper/analysis/fetch_rssi.py`: `--field pressure` downloads the sensor's
  barometric pressure instead of Wi-Fi signal strength, and `--average 360` or
  `1440` requests 6-hour or daily means. The default (hourly rssi) is unchanged.
- `rerun_models.py`, `split_protocols.py`, `generalization_experiments.py`: an optional wider XGBoost
  search (`PA_SEARCH=wide`: depth up to 14, up to 20,000 trees sampled on a log scale, early stopping
  after 100 rounds) and `PA_ONLY` to run named configurations only. Defaults are unchanged.
  `paper/analysis/cluster/` holds the SLURM array job that runs the 28 configurations.
- `paper/analysis/make_figure_s1.py`: Figure S1 also draws the unstratified
  Spatial-National search (same features and target) as a reference curve;
  its numbers are added to `results_50trials/figures/figureS1_caption_numbers.json`.
  `PA_FIG_DIR` draws it into another folder.
- `paper/analysis/make_figure3.py`: the calibrated axis uses at most two
  decimals, so its tick labels no longer run into the y-axis label.
- `paper/figures/generate_figure5.py`: also writes `figure5_pie_shares.json`,
  the group and per-feature SHAP shares behind the pie charts, to two decimals.
- `paper/README.md`: the commands now reproduce the widened search, and the
  scenario figures quoted are those of `results_wide/`.

## [2.1.1] - 2026-11-14

### Added

- `paper/analysis/fetch_rssi.py` and `rssi_test.py`: Wi-Fi signal strength for
  the 98 study sensors from the PurpleAir history API, and a test of whether it
  improves calibration of sensors the model has not seen. It does not
  (1.900 -> 1.903 C), and a per-sensor mean makes unseen sensors worse
  (1.921 C). The checks that the API's sensors, positions and timestamps match
  the paired data are included with their outputs; the downloaded values are
  PurpleAir's and are not redistributed.

### Changed

- The manuscript now reports its newer analyses in the supplementary
  information. `paper/README.md` and the script docstrings point to Sections
  4.2-4.3 and SI Sections S7-S12 accordingly.
- The paired dataset is attached to this release as well, unchanged
  (same SHA-256), so that "download from the latest release" keeps working.

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
