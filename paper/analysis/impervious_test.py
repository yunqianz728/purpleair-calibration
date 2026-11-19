"""Does the ground surface around a sensor (asphalt vs grass) help the calibration? (Reviewer 2, R2.3)

R2 asked whether tree canopy cover is enough to describe shading, since two places with equal canopy
can differ in their ground surface. The revision characterises every sensor and station by NLCD 2021
percent developed imperviousness (SI Sections S10-S11); this adds it to the model, with the design of
rssi_test.py (same five sensor-grouped folds and tuned hyperparameters, so the feature set is the only
change; the baseline is taken from rssi_test.json, the identical fit):

  +impervious      the sensor's percent impervious
  +impervious_gap  sensor minus its reference station, the contrast a sensor-station bias would follow

Both are constant per sensor, so a gain on the random partition with none on unseen sensors would be
site recognition rather than a transferable effect (SI Section S7); hence both partitions are reported.

Input : PA_PARQUET, paper/results_20trials/nlcd_points.csv, <PA_OUT>/models/..., <PA_OUT>/rssi_test.json
Output: <PA_OUT>/impervious_test.json
Usage : PA_PARQUET=paper/analysis/train.parquet PA_OUT=paper/results_wide python3 paper/analysis/impervious_test.py
"""
import json, os, time
import numpy as np, pandas as pd, xgboost as xgb
from sklearn.model_selection import GroupKFold, train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, '..', 'results_wide')
PARQUET = os.environ['PA_PARQUET']
FEATS = json.load(open(os.path.join(HERE, 'feature_sets.json')))['TEMPORAL_FEATURES']
TARGET, SEED, N_JOBS = 'station temperature', 42, 8


def metrics(y, p):
    e = np.asarray(p) - np.asarray(y)
    return {'MAE': round(float(np.mean(np.abs(e))), 4), 'RMSE': round(float(np.sqrt(np.mean(e ** 2))), 4),
            'n': int(len(e))}


def main():
    df = pd.read_parquet(PARQUET)
    nl = pd.read_csv(os.path.join(HERE, '..', 'results_20trials', 'nlcd_points.csv'))
    sens = nl[nl.kind == 'sensor'].assign(sensor_id=lambda d: d.id.astype(int))[['sensor_id', 'impervious_pct']]
    stat = nl[nl.kind != 'sensor'][['id', 'impervious_pct']].rename(columns={'id': 'hadisd_station_id',
                                                                         'impervious_pct': 'station_imp'})
    n0 = len(df)
    df = df.merge(sens.rename(columns={'impervious_pct': 'impervious'}), on='sensor_id', how='left')
    df = df.merge(stat.drop_duplicates('hadisd_station_id'), on='hadisd_station_id', how='left')
    assert len(df) == n0
    df['impervious_gap'] = df['impervious'] - df['station_imp']
    out = {'coverage_%': {c: round(100 * float(df[c].notna().mean()), 1) for c in ['impervious', 'impervious_gap']},
           'sensor_impervious_median': float(df.groupby('sensor_id')['impervious'].first().median())}
    print(json.dumps(out), flush=True)

    best = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))['best_params']
    ref = json.load(open(os.path.join(OUT, 'rssi_test.json')))
    variants = {'+impervious': FEATS + ['impervious'], '+impervious_gap': FEATS + ['impervious_gap']}
    y = df[TARGET].values
    path = os.path.join(OUT, 'impervious_test.json')

    def fit(feats, a):
        m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
        m.fit(df.iloc[a][feats], df.iloc[a][TARGET], sample_weight=df.iloc[a]['Wsample'], verbose=False)
        return m

    folds = list(GroupKFold(n_splits=5).split(df, groups=df['sensor_id']))
    out['leave_sensors_out'] = {'baseline': ref['leave_sensors_out']['baseline']}
    for name, feats in variants.items():
        t0 = time.time(); pred = np.full(len(df), np.nan)
        for a, b in folds:
            pred[b] = fit(feats, a).predict(df.iloc[b][feats])
        out['leave_sensors_out'][name] = metrics(y, pred)
        print(f'leave-sensors-out {name}: {out["leave_sensors_out"][name]} ({time.time() - t0:.0f}s)', flush=True)
        json.dump(out, open(path, 'w'), indent=1)

    tr, te = train_test_split(df.index.values, test_size=0.2, random_state=SEED)
    a, b = df.index.get_indexer(tr), df.index.get_indexer(te)
    out['random_split'] = {'baseline': ref['random_split']['baseline']}
    for name, feats in variants.items():
        out['random_split'][name] = metrics(y[b], fit(feats, a).predict(df.iloc[b][feats]))
        print(f'random split {name}: {out["random_split"][name]}', flush=True)
        json.dump(out, open(path, 'w'), indent=1)
    out['baseline_from'] = 'rssi_test.json (same hyperparameters, folds and partition)'
    json.dump(out, open(path, 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
