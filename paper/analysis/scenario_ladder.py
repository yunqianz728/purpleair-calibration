"""The four deployment scenarios in one table, plus the two checks the Results section quotes.

Collects the four protocols that are each fitted elsewhere -- random rows and leave-sensors-out by
rerun_models.py, blocked-by-week and chronological by split_protocols.py -- into the single
comparison reported in the manuscript, and computes two things that explain why the random split is
the most optimistic of them:

  * adjacency: the share of random-split test rows for which the SAME sensor has a labelled training
    row in the preceding or following hour;
  * a naive neighbour baseline: predict the station temperature of such a row by averaging the
    labelled station temperatures of its adjacent hours, using no model and no features at all.

Also reports the uncalibrated sensor error on each protocol's own test rows, so the percentage
reductions quoted in the text are computed against the matching baseline rather than a global one.

Input : <PA_OUT>/pred_*.parquet, <PA_OUT>/grouped_cv.json, <PA_OUT>/split_protocols/summary.json
Output: <PA_OUT>/scenario_ladder.json
Usage : PA_PARQUET=... PA_OUT=analysis_R1/results50 python3 analysis_R1/scenario_ladder.py
"""
import json, os
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
PARQUET = os.environ.get('PA_PARQUET', '')
CSV = os.path.join(HERE, '..', 'data', 'training_data_with_classification.csv.gz')
SEED = 42
COLS = ['sensor_id', 'datetime', 'sensor temperature', 'station temperature']


def main():
    df = pd.read_parquet(PARQUET, columns=COLS) if PARQUET and os.path.exists(PARQUET) \
        else pd.read_csv(CSV, low_memory=False, usecols=COLS)
    df['datetime'] = pd.to_datetime(df['datetime'])
    raw = (df['sensor temperature'] - df['station temperature']).abs()
    out = {'uncalibrated_MAE_all_rows': round(float(raw.mean()), 3), 'n_rows': int(len(df))}

    # ---- the four protocols, each scored on its own test rows
    lad = {}
    p = pd.read_parquet(os.path.join(BASE, 'pred_Temporal-National__station_temp__National.parquet'))
    te_random = p['row'].values
    lad['random rows'] = {'MAE': float((np.abs(p['pred'].values - df.loc[te_random, 'station temperature'].values)).mean()),
                          'n_test': int(len(p)), 'uncalibrated_MAE': float(raw.loc[te_random].mean())}

    sp = json.load(open(os.path.join(BASE, 'split_protocols', 'summary.json')))
    for key, label in [('week', 'blocked by week'), ('chrono', 'chronological per sensor')]:
        q = pd.read_parquet(os.path.join(BASE, 'split_protocols', f'pred_{key}.parquet'))
        idx = q['row'].values
        lad[label] = {'MAE': sp[key]['test']['MAE'], 'n_test': sp[key]['test']['n'],
                      'per_sensor_abs_bias_median': sp[key]['per_sensor_abs_bias_median'],
                      'RMSE': sp[key]['test']['RMSE'], 'uncalibrated_MAE': float(raw.loc[idx].mean())}

    g = json.load(open(os.path.join(BASE, 'grouped_cv.json')))['Temporal']['overall']
    lad['leave sensors out'] = {'MAE': g['MAE'], 'RMSE': g['RMSE'], 'n_test': g['n'],
                                'uncalibrated_MAE': float(raw.mean())}   # every row is held out in some fold

    # per-sensor bias for the two protocols whose predictions are row-aligned here
    for label, pred, idx in [('random rows', p['pred'].values, te_random),
                             ('leave sensors out',
                              pd.read_parquet(os.path.join(BASE, 'pred_grouped_Temporal.parquet'))['pred'].values,
                              df.index.values)]:
        r = pd.Series(pred - df.loc[idx, 'station temperature'].values, index=idx)
        lad[label]['per_sensor_abs_bias_median'] = float(
            r.groupby(df.loc[idx, 'sensor_id'].values).mean().abs().median())
    lad['random rows']['RMSE'] = float(np.sqrt(((p['pred'].values - df.loc[te_random, 'station temperature'].values) ** 2).mean()))

    for v in lad.values():
        v['reduction_%'] = round(100 * (1 - v['MAE'] / v['uncalibrated_MAE']), 1)
        for k in ('MAE', 'RMSE', 'uncalibrated_MAE', 'per_sensor_abs_bias_median'):
            v[k] = round(v[k], 3)
    out['ladder'] = lad

    # ---- why the random split is the most optimistic: adjacency and a model-free neighbour baseline
    tr_random, _ = train_test_split(df.index.values, test_size=0.2, random_state=SEED)
    key = df['sensor_id'].astype('int64') * 10 ** 11 + (df['datetime'].astype('int64') // 10 ** 9 // 3600)
    labelled = dict(zip(key.loc[tr_random].values, df.loc[tr_random, 'station temperature'].values))
    kt = key.loc[te_random].values
    prev = np.array([labelled.get(k - 1, np.nan) for k in kt])
    nxt = np.array([labelled.get(k + 1, np.nan) for k in kt])
    has = ~(np.isnan(prev) & np.isnan(nxt))
    with np.errstate(invalid='ignore'):
        import warnings
        with warnings.catch_warnings():     # rows with no labelled neighbour are masked out below
            warnings.simplefilter('ignore', RuntimeWarning)
            naive = np.nanmean(np.vstack([prev, nxt]), axis=0)
    y = df.loc[te_random, 'station temperature'].values
    out['adjacency'] = {
        'share_of_test_rows_with_labelled_neighbour_hour': round(float(has.mean()), 3),
        'naive_neighbour_mean_MAE_on_those_rows': round(float(np.abs(naive[has] - y[has]).mean()), 3),
        'model_MAE_on_those_rows': round(float(np.abs(p['pred'].values[has] - y[has]).mean()), 3),
        'model_MAE_on_rows_without_neighbour': round(float(np.abs(p['pred'].values[~has] - y[~has]).mean()), 3),
        'n_without_neighbour': int((~has).sum())}

    json.dump(out, open(os.path.join(BASE, 'scenario_ladder.json'), 'w'), indent=1)
    print(f"uncalibrated MAE, all rows: {out['uncalibrated_MAE_all_rows']}")
    for k, v in lad.items():
        print(f"  {k:26s} MAE {v['MAE']:.3f}  RMSE {v['RMSE']:.3f}  |bias| {v['per_sensor_abs_bias_median']:.3f}"
              f"  raw {v['uncalibrated_MAE']:.2f}  -{v['reduction_%']}%  n={v['n_test']:,}")
    print('adjacency:', json.dumps(out['adjacency']))


if __name__ == '__main__':
    main()
