"""Does Wi-Fi signal strength help calibrate a sensor the model has never seen? (Reviewer 1.4)

R1 suggested Wi-Fi signal strength (rssi) as a proxy for the heat the electronics add inside the
enclosure. The paper argues that at a fixed installation rssi is close to a per-sensor constant, and
that per-sensor constants help the model recognise sites it was trained on rather than calibrate new
ones. This tests that argument directly, on the evaluation where it matters: the same 5-fold
leave-sensors-out split that gives the paper's 1.90 C, with the same tuned hyperparameters, so the
only thing that changes between variants is the feature set.

  baseline     the 63 Temporal features                         (must reproduce grouped_cv.json)
  +rssi        plus hourly rssi                                 (missing hours left as NaN)
  +rssi_mean   plus each sensor's mean rssi over its record     (the "constant" version)

The random-hour split of the main results (Table 2's 0.72 C) is also refitted with and without
hourly rssi, because a feature can help there by identifying sites while failing on new sensors.

Join. fetch_rssi.py saves PurpleAir's own UTC timestamps. The paired dataset advanced every
PurpleAir timestamp by one hour, so a paired row at time_utc is the PurpleAir hour time_utc - 1 h;
rows are joined on (sensor_id, that hour) exactly. fetch_rssi.py --verify-time must report zero lag
before this is run, and this script refuses to run if it has not.

Input : PA_PARQUET, analysis_R1/rssi/raw/*.csv, analysis_R1/rssi/verify_time.json,
        <PA_OUT>/models/Temporal-National__station_temp__National.json, <PA_OUT>/grouped_cv.json
Output: <PA_OUT>/rssi_test.json
Usage : PA_PARQUET=... PA_OUT=analysis_R1/results50 python3 analysis_R1/rssi_test.py
"""
import glob, json, os, sys, time
import numpy as np, pandas as pd, xgboost as xgb
from sklearn.model_selection import GroupKFold, train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, 'results50')
PARQUET = os.environ['PA_PARQUET']
RAW = os.path.join(HERE, 'rssi', 'raw')
FEATS = json.load(open(os.path.join(HERE, 'feature_sets.json')))['TEMPORAL_FEATURES']
TARGET, SEED, N_JOBS = 'station temperature', 42, 8


def metrics(y, p):
    e = np.asarray(p) - np.asarray(y)
    return {'MAE': round(float(np.mean(np.abs(e))), 4), 'RMSE': round(float(np.sqrt(np.mean(e ** 2))), 4),
            'n': int(len(e))}


def load():
    vt = os.path.join(HERE, 'rssi', 'verify_time.json')
    if not os.path.exists(vt):
        sys.exit('run fetch_rssi.py --verify-time first')
    lags = {r['best']['lag_h'] for r in json.load(open(vt)) if r.get('best')}
    if lags != {0}:
        sys.exit(f'timestamps are not aligned (best lags {sorted(lags)}); refusing to join')

    df = pd.read_parquet(PARQUET)
    df['pa_epoch'] = ((pd.to_datetime(df.time_utc, utc=True) - pd.Timedelta(hours=1))
                      .astype('int64') // 10**9)
    parts = []
    for f in glob.glob(os.path.join(RAW, '*.csv')):
        r = pd.read_csv(f).drop_duplicates('time_stamp')
        r['sensor_id'] = int(os.path.basename(f)[:-4])
        parts.append(r)
    rs = pd.concat(parts).rename(columns={'time_stamp': 'pa_epoch'})
    n0 = len(df)
    df = df.merge(rs, on=['sensor_id', 'pa_epoch'], how='left', validate='many_to_one')
    assert len(df) == n0, 'the join changed the number of paired rows'
    df['rssi_mean'] = df.groupby('sensor_id')['rssi'].transform('mean')
    return df


def main():
    df = load()
    cov = df.groupby('sensor_id')['rssi'].apply(lambda s: s.notna().mean())
    within = df.groupby('sensor_id')['rssi'].std()
    between = df.groupby('sensor_id')['rssi'].mean().std()
    out = {'coverage': {'rows_with_rssi_%': round(100 * float(df.rssi.notna().mean()), 1),
                        'sensors_with_any_rssi': int((cov > 0).sum()), 'sensors': int(len(cov)),
                        'per_sensor_coverage_median_%': round(100 * float(cov.median()), 1)},
           'rssi_dBm': {'median': float(df.rssi.median()),
                        'within_sensor_sd_median': round(float(within.median()), 2),
                        'between_sensor_sd_of_means': round(float(between), 2)}}
    print(json.dumps(out, indent=1), flush=True)

    best = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))['best_params']
    variants = {'baseline': FEATS, '+rssi': FEATS + ['rssi'], '+rssi_mean': FEATS + ['rssi_mean']}
    y = df[TARGET].values

    def fit(feats, a):
        m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
        m.fit(df.iloc[a][feats], df.iloc[a][TARGET], sample_weight=df.iloc[a]['Wsample'], verbose=False)
        return m

    folds = list(GroupKFold(n_splits=5).split(df, groups=df['sensor_id']))
    out['leave_sensors_out'] = {}
    for name, feats in variants.items():
        t0 = time.time(); pred = np.full(len(df), np.nan)
        for a, b in folds:
            pred[b] = fit(feats, a).predict(df.iloc[b][feats])
        out['leave_sensors_out'][name] = metrics(y, pred)
        print(f'leave-sensors-out {name}: {out["leave_sensors_out"][name]}  ({time.time() - t0:.0f}s)', flush=True)

    ref = json.load(open(os.path.join(OUT, 'grouped_cv.json')))['Temporal']['overall']['MAE']
    out['baseline_reproduces_paper'] = abs(out['leave_sensors_out']['baseline']['MAE'] - ref) < 0.005
    out['paper_leave_sensors_out_MAE'] = round(ref, 4)

    tr, te = train_test_split(df.index.values, test_size=0.2, random_state=SEED)
    a, b = df.index.get_indexer(tr), df.index.get_indexer(te)
    out['random_split'] = {}
    for name in ['baseline', '+rssi']:
        out['random_split'][name] = metrics(y[b], fit(variants[name], a).predict(df.iloc[b][variants[name]]))
        print(f'random split {name}: {out["random_split"][name]}', flush=True)

    json.dump(out, open(os.path.join(OUT, 'rssi_test.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
