"""Does calibration erase the urban signal? (Reviewer 1)

R1's concern: HadISD reference stations and ERA5 rarely capture urban phenomena, so a model trained to
reproduce the station reading might strip the urban heat signal out of the PurpleAir values.

Inputs: NLCD 2021 percent-impervious at each sensor and each reference station (results/nlcd_points.csv;
sensors median 64 %, stations 24 %) and the leave-sensors-out predictions (pred_grouped_Temporal.parquet),
i.e. the calibrated value a sensor receives when it contributed no training data -- the deployment case
R1 is asking about. All measurements at night (00:00-05:00 local), when the urban heat island is
strongest and the enclosure is not being heated by the sun.

Two framings, which answer different questions:

  A. ACROSS SENSORS, each against its own station: regress the sensor-minus-station night anomaly on
     the sensor-minus-station impervious contrast, with climate-zone means removed. This turns out to
     be a poor urban-signal measure in either the raw or the calibrated data, because each sensor is
     referenced to a different station in a different setting; it is reported to show that explicitly.

  B. WITHIN A SHARED REFERENCE STATION: every pair of sensors reporting to the SAME station and
     differing by at least MIN_GAP points of impervious cover. Both sensors share one reference, so
     their difference is a clean local contrast. This is the measure that matters for hyperlocal
     mapping, which compares nearby sensors with each other rather than with a distant airport.
     Reported both over all pairs and over one pair per station (the extreme pair), since pairs from
     the same station are not independent.

Sensors failing the a-priori QC rule of generalization_experiments.py (daily-mean correlation with the
station < 0.8: not tracking ambient temperature at all) are excluded from the headline numbers and
reported separately, because their between-sensor differences reflect malfunction, not land cover.
Usage: python3 analysis_R1/uhi_preservation.py
"""
import json, os, itertools
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')   # PA_OUT selects the tuning budget
NIGHT = [0, 1, 2, 3, 4, 5]
MIN_GAP = 5          # minimum impervious contrast (percentage points) for a pair to be informative
MIN_ROWS = 100       # minimum night observations per sensor
PARQUET = os.environ.get('PA_PARQUET', '')
CSV = os.path.join(HERE, '..', 'data', 'training_data_with_classification.csv.gz')
COLS = ['sensor_id', 'hadisd_station_id', 'station_name', 'hour',
        'sensor temperature', 'station temperature', 'MainGroup']


def ols(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y)); x, y = x[m], y[m]
    if len(x) < 5:
        return {'n': int(len(x))}
    b, a = np.polyfit(x, y, 1)
    se = float(np.sqrt(np.sum((y - (a + b * x)) ** 2) / (len(x) - 2) / np.sum((x - x.mean()) ** 2)))
    return {'slope_C_per_10pct': round(float(b) * 10, 3), 'se_per_10pct': round(se * 10, 3),
            't': round(float(b) / se, 2), 'r': round(float(np.corrcoef(x, y)[0, 1]), 3), 'n': int(len(x))}


def demeaned_slope(d, col, by='zone'):
    d = d.dropna(subset=['d_imp', col]).copy()
    d['y'] = d[col] - d.groupby(by)[col].transform('mean')
    d['x'] = d['d_imp'] - d.groupby(by)['d_imp'].transform('mean')
    return ols(d.x, d.y)


def pairs_within_station(g):
    rows = []
    for st, d in g.groupby('station'):
        for a, b in itertools.combinations(range(len(d)), 2):
            u, v = d.iloc[a], d.iloc[b]
            if abs(u.s_imp - v.s_imp) < MIN_GAP:
                continue
            hi, lo = (u, v) if u.s_imp > v.s_imp else (v, u)
            rows.append({'station': st, 'name': hi['name'], 'd_imp': float(hi.s_imp - lo.s_imp),
                         'raw_diff': float(hi.raw - lo.raw), 'cal_diff': float(hi.cal - lo.cal)})
    return pd.DataFrame(rows)


def pair_stats(w):
    if len(w) < 5:
        return {'n_pairs': int(len(w))}
    return {'n_pairs': int(len(w)), 'n_stations': int(w.station.nunique()),
            'median_abs_raw_diff': round(float(w.raw_diff.abs().median()), 3),
            'median_abs_cal_diff': round(float(w.cal_diff.abs().median()), 3),
            'raw_vs_impervious': ols(w.d_imp, w.raw_diff),
            'calibrated_vs_impervious': ols(w.d_imp, w.cal_diff),
            'corr_raw_calibrated': round(float(w.cal_diff.corr(w.raw_diff)), 3),
            'sign_agreement_%': round(100 * float((np.sign(w.raw_diff) == np.sign(w.cal_diff)).mean()), 1)}


def main():
    df = pd.read_parquet(PARQUET, columns=COLS) if PARQUET and os.path.exists(PARQUET) \
        else pd.read_csv(CSV, low_memory=False, usecols=COLS)
    df['cal'] = pd.read_parquet(os.path.join(OUT, 'pred_grouped_Temporal.parquet'))['pred'].values
    # NLCD imperviousness does not depend on the tuning budget, so it is written once into
    # the default results dir and reused whatever PA_OUT points at
    nlcd = os.path.join(OUT, 'nlcd_points.csv')
    if not os.path.exists(nlcd):
        nlcd = os.path.join(HERE, 'results', 'nlcd_points.csv')
    nl = pd.read_csv(nlcd, dtype={'id': str})
    s_imp = nl[nl.kind == 'sensor'].set_index('id')['impervious_pct']       # sensor ids are ints in the
    st_imp = nl[nl.kind == 'station'].set_index('id')['impervious_pct']     # dataset, strings in the CSV
    # as with the NLCD layer, the record-quality screen is budget-independent
    qc = os.path.join(OUT, 'generalization', 'qc_flags.json')
    if not os.path.exists(qc):
        qc = os.path.join(HERE, 'results', 'generalization', 'qc_flags.json')
    flagged = set(str(s) for s in json.load(open(qc))['flagged_sensors'])

    df['sid'] = df['sensor_id'].astype(str)
    n = df[df.hour.isin(NIGHT)].copy()
    n['raw_anom'] = n['sensor temperature'] - n['station temperature']
    n['cal_anom'] = n['cal'] - n['station temperature']
    g = n.groupby('sid').agg(raw=('raw_anom', 'mean'), cal=('cal_anom', 'mean'),
                             station=('hadisd_station_id', 'first'), name=('station_name', 'first'),
                             zone=('MainGroup', 'first'), rows=('raw_anom', 'size'))
    g['s_imp'] = g.index.map(s_imp); g['st_imp'] = g['station'].map(st_imp)
    g['d_imp'] = g['s_imp'] - g['st_imp']
    g['qc_flagged'] = g.index.isin(flagged)
    g = g[g.rows >= MIN_ROWS]
    keep = g[~g.qc_flagged].dropna(subset=['d_imp'])

    res = {'night_hours': NIGHT, 'min_impervious_gap_pts': MIN_GAP,
           'n_sensors_total': int(len(g)), 'n_sensors_qc_flagged': int(g.qc_flagged.sum()),
           'n_sensors_used': int(len(keep)),
           'impervious_median': {'sensor': float(keep.s_imp.median()), 'station': float(keep.st_imp.median()),
                                 'contrast': float(keep.d_imp.median())},
           'A_across_sensors_zone_demeaned': {
               'raw': demeaned_slope(keep, 'raw'), 'calibrated': demeaned_slope(keep, 'cal'),
               'note': 'each sensor referenced to a different station; weak in both -- see docstring'},
           'A_including_qc_flagged': {
               'raw': demeaned_slope(g.dropna(subset=['d_imp']), 'raw'),
               'calibrated': demeaned_slope(g.dropna(subset=['d_imp']), 'cal')}}

    w = pairs_within_station(keep)
    res['B_within_station_all_pairs'] = pair_stats(w)
    if len(w):
        ext = w.loc[w.groupby('station').d_imp.idxmax()]      # one independent pair per station
        res['B_within_station_one_per_station'] = pair_stats(ext)
        w.round(3).to_csv(os.path.join(OUT, 'uhi_within_station_pairs.csv'), index=False)
    wf = pairs_within_station(g.dropna(subset=['d_imp']))
    res['B_including_qc_flagged'] = pair_stats(wf)

    urb, rur = keep[keep.s_imp >= 50], keep[keep.s_imp < 50]
    res['urban_vs_rural_sensors'] = {
        'n_urban': int(len(urb)), 'n_rural': int(len(rur)),
        'raw_night_anomaly': {'urban': round(float(urb.raw.mean()), 3), 'rural': round(float(rur.raw.mean()), 3)},
        'calibrated_night_anomaly': {'urban': round(float(urb.cal.mean()), 3), 'rural': round(float(rur.cal.mean()), 3)}}

    g.round(3).to_csv(os.path.join(OUT, 'uhi_per_sensor.csv'))
    json.dump(res, open(os.path.join(OUT, 'uhi_preservation.json'), 'w'), indent=1)
    print(json.dumps(res, indent=1, default=float))


if __name__ == '__main__':
    main()
