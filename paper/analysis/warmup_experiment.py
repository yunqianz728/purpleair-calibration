"""How long must a new sensor be paired with a reference station? (R1, 'short time series' comment.)

Reviewer 1 notes that short PurpleAir records (e.g. one month) should still be usable for calibration.
This quantifies that. Starting from the leave-sensors-out setting (a sensor with NO labelled data of its
own, MAE 1.900), we give each test sensor its earliest N days of LABELLED rows as extra training data
and measure what that buys.

Protocol
  * the same 5-fold GroupKFold by sensor as rerun_models.py `grouped`;
  * only test sensors with a record longer than WINDOW days are evaluated (81 of 98 sensors);
  * the evaluation window is FIXED at rows after day WINDOW of each sensor's own record, identical for
    every N, so the warm-up lengths are compared on exactly the same 630,913 test rows;
  * training rows = all rows of the fold's training sensors + the test sensors' rows before day N;
  * hyperparameters are the ones tuned for the national model in the main run and are held fixed across
    N (noted as such): re-tuning per N would confound the comparison.
  * N = 0 reproduces the leave-sensors-out baseline on this restricted test set.

Writes results/warmup/summary.json (overall, per-zone and per-sensor metrics for each N) and, per N,
the predictions needed for figures.
Usage: python3 analysis_R1/warmup_experiment.py
"""
import json, os, time
import numpy as np, pandas as pd, xgboost as xgb
from sklearn.model_selection import GroupKFold
from rerun_models import load, metrics, FEATURES, OUT, SEED, N_JOBS, log

WU = os.path.join(OUT, 'warmup'); os.makedirs(WU, exist_ok=True)
FEATS = FEATURES['Temporal']
TARGET = 'station temperature'
WINDOW = 90                      # evaluation starts after this day of each sensor's own record
WARMUPS = [0, 7, 14, 30, 90]     # days of the test sensor's own labelled data added to training


def main():
    df = load(); log(f'warmup: data {df.shape}')
    t = pd.to_datetime(df['datetime'])
    day = (t - t.groupby(df['sensor_id']).transform('min')).dt.days.values
    span = (t.groupby(df['sensor_id']).max() - t.groupby(df['sensor_id']).min()).dt.days
    long_enough = df['sensor_id'].isin(span[span > WINDOW].index).values
    y = df[TARGET].values; w = df['Wsample'].values
    groups = df['sensor_id'].values
    X = df[FEATS]
    best = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))['best_params']
    folds = list(GroupKFold(n_splits=5).split(df, groups=groups))
    log(f'warmup: {int(span.gt(WINDOW).sum())} sensors with span > {WINDOW}d, '
        f'{int((long_enough & (day >= WINDOW)).sum())} evaluation rows, params {best}')
    summary = {}
    for N in WARMUPS:
        pred = np.full(len(df), np.nan)
        for k, (a, b) in enumerate(folds):
            ppath = os.path.join(WU, f'N{N}_fold{k}.npz')
            if os.path.exists(ppath):
                z = np.load(ppath); pred[z['idx']] = z['pred']; continue
            t0 = time.time()
            te = b[long_enough[b] & (day[b] >= WINDOW)]
            if len(te) == 0:
                np.savez(ppath, idx=te, pred=np.array([])); continue
            warm = b[long_enough[b] & (day[b] < N)] if N > 0 else np.array([], dtype=int)
            tr = np.concatenate([a, warm])
            m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist',
                                 random_state=SEED, n_jobs=N_JOBS)
            m.fit(X.iloc[tr], y[tr], sample_weight=w[tr], verbose=False)
            p = m.predict(X.iloc[te]); pred[te] = p
            np.savez(ppath, idx=te, pred=p)
            log(f'warmup N={N} fold {k}: MAE {np.mean(np.abs(p - y[te])):.3f} '
                f'(+{len(warm)} warm-up rows) | {round(time.time() - t0)}s')
        sel = ~np.isnan(pred)
        ps = pd.Series(np.abs(pred[sel] - y[sel])).groupby(groups[sel]).mean()
        bias = pd.Series(pred[sel] - y[sel]).groupby(groups[sel]).mean()
        summary[f'N{N}'] = {
            'warmup_days': N, 'n_eval_rows': int(sel.sum()), 'n_sensors': int(ps.size),
            'overall': metrics(y[sel], pred[sel]),
            'per_sensor_MAE_q': ps.quantile([0.1, 0.5, 0.9]).round(3).to_dict(),
            'per_sensor_abs_bias_median': float(bias.abs().median()),
            'by_zone': {z: metrics(y[sel & (df.MainGroup.values == z)], pred[sel & (df.MainGroup.values == z)])
                        for z in ['B_Arid', 'C_Temperate', 'D_Continental']}}
        pd.DataFrame({'pred': pred}).to_parquet(os.path.join(WU, f'pred_N{N}.parquet'))
        log(f"warmup N={N}: MAE {summary[f'N{N}']['overall']['MAE']:.3f} "
            f"per-sensor median {summary[f'N{N}']['per_sensor_MAE_q'][0.5]:.3f} "
            f"|bias| {summary[f'N{N}']['per_sensor_abs_bias_median']:.3f}")
        json.dump(summary, open(os.path.join(WU, 'summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
