"""Does the sensor's own barometric pressure help calibrate a sensor the model has never seen? (R1.6)

Reviewer 1 suggested adding the BME280's pressure reading to the calibration. Across the study sites
pressure is set almost entirely by elevation, which is already a predictor, so what pressure could
add is its variation at a fixed site: the synoptic part, which tracks weather. This tests both, with
the design of rssi_test.py (same five sensor-grouped folds, same tuned hyperparameters, so the
feature set is the only change):

  baseline        the 63 Temporal features   (taken from <PA_OUT>/rssi_test.json, the identical fit)
  +pressure       plus hourly pressure (hPa)
  +pressure_anom  plus pressure minus the sensor's own mean: the synoptic part alone
  +pressure_anom_lag  the same from the last day already ended (PA_PRESSURE_EXTRA=1; causal, see below)

and refits the random-hour split with +pressure. Readings outside 500-1100 hPa are treated as
missing.

Resolution. Pressure costs 2 API points per returned row, so the remaining balance allowed daily means
(fetch_rssi.py --field pressure --average 1440, about 77,000 points) but not 6-hour or hourly values.
Daily means resolve the synoptic changes (fronts and pressure systems lasting one to three days), the
part of the signal elevation cannot carry; what they miss is the sub-daily variation, mainly the
~1 hPa semidiurnal tide. Each mean is placed at the centre of its day and interpolated linearly to the
paired hours; an hour more than 24 h from the nearest mean is left missing, so gaps are not bridged.
PA_PRESSURE_RAW and PA_PRESSURE_AVG (minutes) select another download. As a check that the field is what it should be, the sensors' mean pressure is compared with
the pressure their elevation implies (standard atmosphere).

Join: as in rssi_test.py (PurpleAir hour = paired time_utc - 1 h, verified by fetch_rssi.py --verify-time).

Input : PA_PARQUET, paper/analysis/pressure/raw/*.csv, paper/analysis/rssi/verify_time.json,
        <PA_OUT>/models/Temporal-National__station_temp__National.json, <PA_OUT>/rssi_test.json
Output: <PA_OUT>/pressure_test.json
Usage : PA_PARQUET=paper/analysis/train.parquet PA_OUT=paper/results_wide python3 paper/analysis/pressure_test.py
"""
import glob, json, os, sys, time
import numpy as np, pandas as pd, xgboost as xgb
from sklearn.model_selection import GroupKFold, train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, '..', 'results_wide')
PARQUET = os.environ['PA_PARQUET']
AVG_MIN = int(os.environ.get('PA_PRESSURE_AVG', 1440))
RAW = os.environ.get('PA_PRESSURE_RAW') or os.path.join(
    HERE, 'pressure' if AVG_MIN == 60 else f'pressure_{AVG_MIN}min', 'raw')
FEATS = json.load(open(os.path.join(HERE, 'feature_sets.json')))['TEMPORAL_FEATURES']
TARGET, SEED, N_JOBS = 'station temperature', 42, 8
VALID = (500.0, 1100.0)      # hPa; anything outside is a faulty reading


def metrics(y, p):
    e = np.asarray(p) - np.asarray(y)
    return {'MAE': round(float(np.mean(np.abs(e))), 4), 'RMSE': round(float(np.sqrt(np.mean(e ** 2))), 4),
            'n': int(len(e))}


def load():
    vt = os.path.join(HERE, 'rssi', 'verify_time.json')
    lags = {r['best']['lag_h'] for r in json.load(open(vt)) if r.get('best')}
    if lags != {0}:
        sys.exit(f'timestamps are not aligned (best lags {sorted(lags)}); refusing to join')
    df = pd.read_parquet(PARQUET)
    df['pa_epoch'] = ((pd.to_datetime(df.time_utc, utc=True) - pd.Timedelta(hours=1)).astype('int64') // 10**9)
    files = glob.glob(os.path.join(RAW, '*.csv'))
    if not files:
        sys.exit(f'no pressure files in {RAW}; run fetch_rssi.py --field pressure --average {AVG_MIN} first')
    half, reach = AVG_MIN * 30, max(AVG_MIN, 60) * 60          # seconds: half a period; how far to carry a value
    parts = []
    for f in files:
        sid = int(os.path.basename(f)[:-4])
        r = pd.read_csv(f).drop_duplicates('time_stamp')
        r = r[r['pressure'].between(*VALID)]
        hours = np.sort(df.loc[df.sensor_id == sid, 'pa_epoch'].unique())
        if r.empty or not len(hours):
            continue
        t = (r['time_stamp'] + (half if AVG_MIN > 60 else 0)).to_numpy(float)   # centre of each period
        order = np.argsort(t); t, v = t[order], r['pressure'].to_numpy(float)[order]
        p = np.interp(hours, t, v, left=np.nan, right=np.nan)
        i = np.clip(np.searchsorted(t, hours), 1, len(t) - 1) if len(t) > 1 else np.zeros(len(hours), int)
        dist = np.minimum(np.abs(hours - t[i - 1 if len(t) > 1 else i]), np.abs(t[i] - hours))   # to the nearest mean
        p[dist > reach] = np.nan                                  # do not bridge gaps
        # causal version: the most recent period that has ended by the start of the hour, so no value
        # draws on readings later than the hour itself (the interpolation above uses the next mean too)
        ends = np.sort(r['time_stamp'].to_numpy(float)) + AVG_MIN * 60
        vals = r.sort_values('time_stamp')['pressure'].to_numpy(float)
        j = np.searchsorted(ends, hours, side='right') - 1
        lag = np.where(j >= 0, vals[np.clip(j, 0, None)], np.nan)
        lag[(j < 0) | (hours - ends[np.clip(j, 0, None)] >= AVG_MIN * 60)] = np.nan   # only the period just ended
        parts.append(pd.DataFrame({'sensor_id': sid, 'pa_epoch': hours, 'pressure': p, 'pressure_lag': lag}))
    ps = pd.concat(parts)
    n0 = len(df)
    df = df.merge(ps, on=['sensor_id', 'pa_epoch'], how='left', validate='many_to_one')
    assert len(df) == n0, 'the join changed the number of paired rows'
    df['pressure_anom'] = df['pressure'] - df.groupby('sensor_id')['pressure'].transform('mean')
    df['pressure_anom_lag'] = df['pressure_lag'] - df.groupby('sensor_id')['pressure'].transform('mean')
    return df


def extra(df, fit, y, out_path):
    """PA_PRESSURE_EXTRA=1: the causal anomaly on unseen sensors, and both anomalies on the random split,
    added to an existing pressure_test.json without refitting what it already holds."""
    out = json.load(open(out_path))
    feats = FEATS + ['pressure_anom_lag']
    out['coverage']['rows_with_pressure_lag_%'] = round(100 * float(df.pressure_lag.notna().mean()), 1)
    folds = list(GroupKFold(n_splits=5).split(df, groups=df['sensor_id']))
    t0 = time.time(); pred = np.full(len(df), np.nan)
    for a, b in folds:
        pred[b] = fit(feats, a).predict(df.iloc[b][feats])
    out['leave_sensors_out']['+pressure_anom_lag'] = metrics(y, pred)
    print(f'leave-sensors-out +pressure_anom_lag: {out["leave_sensors_out"]["+pressure_anom_lag"]}  ({time.time() - t0:.0f}s)', flush=True)
    json.dump(out, open(out_path, 'w'), indent=1)
    tr, te = train_test_split(df.index.values, test_size=0.2, random_state=SEED)
    a, b = df.index.get_indexer(tr), df.index.get_indexer(te)
    for name in ['+pressure_anom', '+pressure_anom_lag']:
        f = FEATS + [name[1:]]
        out['random_split'][name] = metrics(y[b], fit(f, a).predict(df.iloc[b][f]))
        print(f'random split {name}: {out["random_split"][name]}', flush=True)
        json.dump(out, open(out_path, 'w'), indent=1)
    out['note_lag'] = ('pressure_anom_lag: the daily mean of the UTC day that ended last before the hour, minus the '
                       "sensor's mean; uses no reading later than the hour")
    json.dump(out, open(out_path, 'w'), indent=1)
    print(json.dumps(out, indent=1))


def main():
    df = load()
    cov = df.groupby('sensor_id')['pressure'].apply(lambda s: s.notna().mean())
    means = df.groupby('sensor_id').agg(p=('pressure', 'mean'), elev=('elevation_sensor', 'first'))
    means['p_std_atm'] = 1013.25 * (1 - 2.25577e-5 * means.elev) ** 5.25588
    ok = means.dropna()
    out = {'coverage': {'rows_with_pressure_%': round(100 * float(df.pressure.notna().mean()), 1),
                        'sensors_with_any': int((cov > 0).sum()), 'sensors': int(len(cov))},
           'pressure_hPa': {'median': round(float(df.pressure.median()), 1),
                            'within_sensor_sd_median': round(float(df.groupby('sensor_id')['pressure'].std().median()), 2),
                            'between_sensor_sd_of_means': round(float(means.p.std()), 2)},
           'check_vs_elevation': {'r': round(float(np.corrcoef(ok.p, ok.p_std_atm)[0, 1]), 3),
                                  'median_abs_diff_hPa': round(float((ok.p - ok.p_std_atm).abs().median()), 1)}}
    print(json.dumps(out, indent=1), flush=True)

    best = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))['best_params']
    ref = json.load(open(os.path.join(OUT, 'rssi_test.json')))
    variants = {'+pressure': FEATS + ['pressure'], '+pressure_anom': FEATS + ['pressure_anom']}
    y = df[TARGET].values

    def fit(feats, a):
        m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
        m.fit(df.iloc[a][feats], df.iloc[a][TARGET], sample_weight=df.iloc[a]['Wsample'], verbose=False)
        return m

    if os.environ.get('PA_PRESSURE_EXTRA'):
        return extra(df, fit, y, os.path.join(OUT, 'pressure_test.json'))
    folds = list(GroupKFold(n_splits=5).split(df, groups=df['sensor_id']))
    out['leave_sensors_out'] = {'baseline': ref['leave_sensors_out']['baseline']}
    for name, feats in variants.items():
        t0 = time.time(); pred = np.full(len(df), np.nan)
        for a, b in folds:
            pred[b] = fit(feats, a).predict(df.iloc[b][feats])
        out['leave_sensors_out'][name] = metrics(y, pred)
        print(f'leave-sensors-out {name}: {out["leave_sensors_out"][name]}  ({time.time() - t0:.0f}s)', flush=True)
        json.dump(out, open(os.path.join(OUT, 'pressure_test.json'), 'w'), indent=1)   # keep partial results

    tr, te = train_test_split(df.index.values, test_size=0.2, random_state=SEED)
    a, b = df.index.get_indexer(tr), df.index.get_indexer(te)
    out['random_split'] = {'baseline': ref['random_split']['baseline'],
                           '+pressure': metrics(y[b], fit(variants['+pressure'], a).predict(df.iloc[b][variants['+pressure']]))}
    print(f'random split +pressure: {out["random_split"]["+pressure"]}', flush=True)
    out['baseline_from'] = 'rssi_test.json (same hyperparameters, folds and partition)'
    out['pressure_resolution_min'] = AVG_MIN
    json.dump(out, open(os.path.join(OUT, 'pressure_test.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
