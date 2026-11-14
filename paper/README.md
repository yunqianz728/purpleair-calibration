# Evaluation code for the paper

This directory holds the analysis behind *Nationwide Evaluation and Calibration of PurpleAir
Temperature Sensors for Urban Thermal Environment Research*: the scripts that fit and score every
model configuration, the scripts that answer each reviewer question, the figure code, and the
outputs they produced. Running them reproduces the numbers in the manuscript and the supplementary
information.

This is separate from the deployment app in `app/`. The app serves two models trained for live use;
what follows is the evaluation that the paper reports.

## What you need first

One file: the paired PurpleAir–HadISD dataset, 797,744 hourly observations with all 63 engineered
features. See [`../data/README.md`](../data/README.md) for where to get it; it belongs at
`data/training_data_with_classification.csv.gz`.

Then convert it once, because every script reads the same table and Parquet loads in a second where
gzipped CSV takes a minute:

```bash
pip install pandas numpy scikit-learn xgboost pyarrow scipy
python3 paper/analysis/make_parquet.py
export PA_PARQUET="$PWD/paper/analysis/train.parquet"
```

`PA_OUT` selects where results are written and read; the two directories here were produced with
`PA_OUT=paper/results_50trials` and `PA_OUT=paper/results_20trials`.

## Running it

`rerun_models.py` is the one to start with: it fits all 14 configurations for both targets and
writes a record per model. The rest depend on its output.

```bash
PA_OUT=paper/results_50trials python3 paper/analysis/rerun_models.py     # hours, not minutes
PA_OUT=paper/results_50trials python3 paper/analysis/make_table2.py      # Table 2
```

`run_queue.sh` runs the remaining experiments in sequence; each is resumable, so an interrupted run
picks up where it stopped.

## What each script answers

| Script | Produces |
|---|---|
| `rerun_models.py` | every configuration in Table 2, one JSON per model with metrics, hyperparameters and trial history |
| `make_table2.py` | Table 2 itself |
| `split_protocols.py` | the chronological and blocked-by-week protocols of Section 4.2 |
| `scenario_ladder.py` | the four deployment scenarios, 0.72 / 0.94 / 1.13 / 1.90 °C |
| `warmup_experiment.py` | Table 4: how much of a new sensor's error a week, a month or a season of its own record recovers |
| `generalization_experiments.py` | leave-sensors-out performance, and the effect of dropping per-sensor constants |
| `grouped_sensitivity.py` | GroupKFold over sensors |
| `correlated_features.py` | the 7 correlation clusters, the 37-feature model, the feature-count curve |
| `feature_correlation.py` | the pairwise correlation matrix behind them |
| `shap_export.py`, `make_si_shap_tables.py` | SI Tables S6–S7 and the cluster-aggregated importances |
| `humidity_regimes.py` | Section 4.5: the Temperate zone split by summer dewpoint |
| `uhi_preservation.py` | Section 4.6: whether calibration erases the urban heat signal |
| `nlcd_points.py`, `selected_vs_unselected_stations.py` | imperviousness at every sensor and station, and the retained stations against 500 that were not |
| `lcz_points.py` | Local Climate Zone at the same points, sampled from the global map over HTTP |
| `bias_vs_impervious_gap.py` | whether the raw warm bias scales with the sensor–station imperviousness gap |
| `error_timing.py` | the diurnal and seasonal error patterns of Figure 3 |
| `per_sensor_mae.py` | per-sensor error by climate zone, the distribution in Figure 4(b) |
| `compare_budgets.py` | the 20-trial and 50-trial tuning budgets against each other |
| `make_figure3.py`, `make_figure_s1.py`, `figures/*` | the figures |

## Reanalysis inputs

The feature table already contains the sampled ERA5 values at every observation, so nothing needs
downloading to reproduce the models. `data/download_era5.py` is for rebuilding those columns from
the gridded archives, or extending the dataset: it requests exactly what the paper used, which is
two different products — ERA5-Land at 0.1° for radiation, sensible heat flux and precipitation, and
ERA5 single levels at 0.25° for the 10 m wind components.

## What is not here

- **The fitted model files.** The `.ubj` boosters come to about 700 MB. The JSON record beside each
  one carries its metrics, its hyperparameters and its full trial history, which is what the paper
  reports; `rerun_models.py` refits them from the same seed.
- **The four-algorithm comparison** (SI Table S5). LightGBM, CatBoost and RandomForest were fitted
  under the earlier 20-trial budget and were not refitted under the protocol used here; the
  supplementary information says so where that table appears. `results_20trials/` holds that run.
- **The script that checks the manuscript against these outputs.** It reads the LaTeX source, which
  is not part of this repository.
