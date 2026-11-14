"""Splitting the temperate zone by humidity regime (Reviewer 2).

R2: the Koppen C (temperate) zone lumps the humid southeast with the dry west; electronic sensors are
affected by humidity, and the IECC zones separate temperature (1-8) from humidity (A moist / B dry),
so the temperate data could be split and the error characteristics compared across regimes.

Split: mean SUMMER (JJA) dewpoint measured by the sensors themselves, which is the quantity R2's
concern is about (the humidity the sensor actually experiences) and needs no external map. Within the
temperate zone the two groups separate without overlap -- western sensors (CA, OR, WA) run 6.2-14.3 C
and eastern ones (MD, TX, OK, TN, SC) 16.6-22.2 C -- so any threshold in the gap gives the same
grouping; THRESH sits in the middle of it. The split reproduces the geography R2 describes and
corresponds to IECC moist (A) versus dry/marine (B/C).

Reported for each regime: the raw sensor bias by hour (does the overheating behave differently where
the air is humid?), the calibrated error from both evaluation protocols, and whether the national
model's residual depends on humidity within each regime. Sensors failing the a-priori QC rule of
generalization_experiments.py are excluded from the headline numbers.
Usage: python3 analysis_R1/humidity_regimes.py
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')   # PA_OUT selects the tuning budget
THRESH = 15.0        # C summer mean dewpoint; the observed gap runs 14.3 -> 16.6
MIN_SUMMER = 200     # minimum JJA observations for a sensor to be classified
NIGHT, MIDDAY = [0, 1, 2, 3, 4, 5], [11, 12, 13, 14, 15]
PARQUET = os.environ.get('PA_PARQUET', '')
CSV = os.path.join(HERE, '..', 'data', 'training_data_with_classification.csv.gz')
COLS = ['sensor_id', 'state', 'MainGroup', 'month', 'hour', 'dewpoint_sensor', 'humidity',
        'sensor temperature', 'station temperature', 'sensor_lon']


def describe(d, raw, cal_t, cal_l):
    def mae(v, m=None):
        v = v if m is None else v[m]
        return round(float(np.abs(v).mean()), 3) if len(v) else None

    def bias(v, m=None):
        v = v if m is None else v[m]
        return round(float(v.mean()), 3) if len(v) else None
    night, mid = d.hour.isin(NIGHT).values, d.hour.isin(MIDDAY).values
    out = {'n_rows': int(len(d)), 'n_sensors': int(d.sensor_id.nunique()),
           'summer_dewpoint_C': round(float(d.loc[d.month.isin([6, 7, 8]), 'dewpoint_sensor'].mean()), 2),
           'mean_RH_%': round(float(d.humidity.mean()), 1),
           'raw': {'bias_all': bias(raw), 'bias_night': bias(raw, night), 'bias_midday': bias(raw, mid),
                   'MAE_all': mae(raw)}}
    if cal_t is not None:
        out['calibrated_test_split'] = {'MAE': mae(cal_t[0]), 'bias': bias(cal_t[0]),
                                        'MAE_night': mae(cal_t[0], cal_t[1]), 'MAE_midday': mae(cal_t[0], cal_t[2]),
                                        'n': int(len(cal_t[0]))}
    out['calibrated_leave_sensors_out'] = {'MAE': mae(cal_l), 'bias': bias(cal_l),
                                           'MAE_night': mae(cal_l, night), 'MAE_midday': mae(cal_l, mid)}
    return out


def main():
    df = pd.read_parquet(PARQUET, columns=COLS) if PARQUET and os.path.exists(PARQUET) \
        else pd.read_csv(CSV, low_memory=False, usecols=COLS)
    # the record-quality screen is an a-priori property of the sensors, not of the tuning
    # budget, so it is written once into the default results dir and reused whatever PA_OUT is
    qc = os.path.join(OUT, 'generalization', 'qc_flags.json')
    if not os.path.exists(qc):
        qc = os.path.join(HERE, 'results', 'generalization', 'qc_flags.json')
    flagged = set(json.load(open(qc))['flagged_sensors'])

    summer = df[df.month.isin([6, 7, 8])].groupby('sensor_id').agg(Td=('dewpoint_sensor', 'mean'),
                                                                   n=('dewpoint_sensor', 'size'))
    summer = summer[summer.n >= MIN_SUMMER]
    regime = np.where(summer.Td >= THRESH, 'Moist', 'Dry')
    reg = pd.Series(regime, index=summer.index)
    df['regime'] = df['sensor_id'].map(reg)
    df['qc_flagged'] = df['sensor_id'].isin(flagged)

    # gap check: the split must not depend on the exact threshold
    td = summer.Td.sort_values()
    tc = summer[df.groupby('sensor_id').MainGroup.first().reindex(summer.index) == 'C_Temperate'].Td.sort_values()
    gap = tc.diff().idxmax()
    res = {'threshold_C': THRESH, 'min_summer_obs': MIN_SUMMER,
           'temperate_gap': {'below': round(float(tc[tc < THRESH].max()), 2),
                             'above': round(float(tc[tc >= THRESH].min()), 2),
                             'largest_gap_at_sensor': int(gap)},
           'n_sensors_classified': int(len(summer)), 'n_qc_flagged_excluded': len(flagged)}

    d = df[df.regime.notna() & ~df.qc_flagged].copy()
    raw = (d['sensor temperature'] - d['station temperature']).values
    pl = pd.read_parquet(os.path.join(OUT, 'pred_grouped_Temporal.parquet'))['pred'].values
    cal_l = pl[d.index.values] - d['station temperature'].values
    pt = pd.read_parquet(os.path.join(OUT, 'pred_Temporal-National__station_temp__National.parquet'))
    tmap = pd.Series(pt['pred'].values, index=pt['row'].values)
    in_test = d.index.isin(tmap.index)

    res['regimes'] = {}
    for name in ['Dry', 'Moist']:
        m = (d.regime == name).values
        sub = d[m]
        tm = in_test & m
        ct = None
        if tm.sum():
            e = tmap.loc[d.index[tm]].values - d.loc[d.index[tm], 'station temperature'].values
            ct = (e, d.loc[d.index[tm], 'hour'].isin(NIGHT).values, d.loc[d.index[tm], 'hour'].isin(MIDDAY).values)
        res['regimes'][name] = describe(sub, raw[m], ct, cal_l[m])
        res['regimes'][name]['states'] = sorted(sub.state.dropna().unique().tolist())
        res['regimes'][name]['zones'] = sub.MainGroup.value_counts().to_dict()

    # temperate zone only -- the comparison R2 actually asks for
    res['temperate_only'] = {}
    for name in ['Dry', 'Moist']:
        m = ((d.regime == name) & (d.MainGroup == 'C_Temperate')).values
        if m.sum() == 0:
            continue
        sub = d[m]
        tm = in_test & m
        ct = None
        if tm.sum():
            e = tmap.loc[d.index[tm]].values - d.loc[d.index[tm], 'station temperature'].values
            ct = (e, d.loc[d.index[tm], 'hour'].isin(NIGHT).values, d.loc[d.index[tm], 'hour'].isin(MIDDAY).values)
        res['temperate_only'][name] = describe(sub, raw[m], ct, cal_l[m])
        res['temperate_only'][name]['states'] = sorted(sub.state.dropna().unique().tolist())

    # does the residual still depend on humidity inside each regime?
    res['residual_vs_humidity'] = {}
    for name in ['Dry', 'Moist']:
        m = (d.regime == name).values
        h = d.humidity.values[m]; e = np.abs(cal_l[m])
        q = pd.Series(pd.qcut(h, 4, labels=['Q1_dry', 'Q2', 'Q3', 'Q4_humid'], duplicates='drop'))
        res['residual_vs_humidity'][name] = {str(k): round(float(e[(q == k).values].mean()), 3)
                                             for k in q.cat.categories}

    pd.DataFrame({'sensor_id': summer.index, 'summer_Td': summer.Td.round(2), 'regime': regime}) \
        .to_csv(os.path.join(OUT, 'sensor_humidity_regime_split.csv'), index=False)
    json.dump(res, open(os.path.join(OUT, 'humidity_regimes.json'), 'w'), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == '__main__':
    main()
