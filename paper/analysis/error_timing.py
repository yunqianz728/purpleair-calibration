"""Figure 3: why calibrated error peaks later than raw error, and what the October peak is (Reviewer 2).

R2: "It is surprising that the peak MAE for the calibrated sensor error seems to lag the peak for the
uncalibrated error for both the seasonal and diurnal patterns", nothing is said about the small
seasonal peak around October, and the claim about physical error mechanisms being most complex is
unsupported.

This quantifies all three on the re-run national model (Temporal-National, target T_station):
  * diurnal and seasonal MAE of the uncalibrated sensor and of the calibrated value, with the peak
    hour/month of each and the lag between them;
  * what distinguishes the lag hours: the raw bias tracks incoming solar radiation, while the
    calibrated residual tracks how fast the air temperature is CHANGING (the enclosure's thermal
    memory is a lagged response, so the hardest hours to correct are the ones where the lag terms are
    least informative -- the late-afternoon/evening cooling transition, not solar noon);
  * October: the month's radiation, diurnal range, humidity and wind, compared with its neighbours,
    to see which of them the October error follows.

Predictions: the national model's own held-out test rows (results/pred_Temporal-National__*.parquet),
which is the basis Figure 3 is drawn on; the leave-sensors-out predictions are reported alongside as a
robustness check.
Usage: python3 analysis_R1/error_timing.py
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')   # PA_OUT selects the tuning budget
PARQUET = os.environ.get('PA_PARQUET', '')
CSV = os.path.join(HERE, '..', 'data', 'training_data_with_classification.csv.gz')
COLS = ['sensor_id', 'hour', 'month', 'sensor temperature', 'station temperature',
        'ssrd', 'humidity', 'wind_speed', 'temp_change_1h', 'temp_trend_6h', 'MainGroup']
MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def profile(d, key, raw, cal):
    g = d.groupby(key)
    out = pd.DataFrame({'n': g.size(),
                        'raw_MAE': g.apply(lambda x: np.abs(raw[x.index]).mean()),
                        'raw_bias': g.apply(lambda x: raw[x.index].mean()),
                        'cal_MAE': g.apply(lambda x: np.abs(cal[x.index]).mean()),
                        'cal_bias': g.apply(lambda x: cal[x.index].mean())})
    return out.round(3)


def main():
    df = pd.read_parquet(PARQUET, columns=COLS) if PARQUET and os.path.exists(PARQUET) \
        else pd.read_csv(CSV, low_memory=False, usecols=COLS)
    res = {}

    for tag, pred_file, idx_col in [('test_split', 'pred_Temporal-National__station_temp__National.parquet', 'row'),
                                    ('leave_sensors_out', 'pred_grouped_Temporal.parquet', None)]:
        p = pd.read_parquet(os.path.join(OUT, pred_file))
        if idx_col:
            d = df.loc[p[idx_col].values].copy(); cal_pred = p['pred'].values
        else:
            d = df.copy(); cal_pred = p['pred'].values
        d = d.reset_index(drop=True)
        raw = pd.Series(d['sensor temperature'].values - d['station temperature'].values)
        cal = pd.Series(cal_pred - d['station temperature'].values)

        hourly = profile(d, 'hour', raw, cal)
        monthly = profile(d, 'month', raw, cal)
        hr_raw, hr_cal = int(hourly.raw_MAE.idxmax()), int(hourly.cal_MAE.idxmax())
        mo_raw, mo_cal = int(monthly.raw_MAE.idxmax()), int(monthly.cal_MAE.idxmax())
        res[tag] = {
            'hourly': hourly.to_dict('index'), 'monthly': monthly.to_dict('index'),
            'diurnal_peak': {'raw_hour': hr_raw, 'calibrated_hour': hr_cal, 'lag_hours': hr_cal - hr_raw,
                             'raw_MAE_at_peak': float(hourly.raw_MAE.max()),
                             'cal_MAE_at_peak': float(hourly.cal_MAE.max())},
            'seasonal_peak': {'raw_month': MONTH[mo_raw - 1], 'calibrated_month': MONTH[mo_cal - 1],
                              'lag_months': mo_cal - mo_raw},
            'october': {'cal_MAE': float(monthly.loc[10, 'cal_MAE']),
                        'vs_sep': round(float(monthly.loc[10, 'cal_MAE'] - monthly.loc[9, 'cal_MAE']), 3),
                        'vs_nov': round(float(monthly.loc[10, 'cal_MAE'] - monthly.loc[11, 'cal_MAE']), 3)}}

        if tag == 'test_split':
            # what the two error series track, hour by hour
            hv = d.groupby('hour').agg(ssrd=('ssrd', 'mean'), humidity=('humidity', 'mean'),
                                       wind=('wind_speed', 'mean'),
                                       abs_dT=('temp_change_1h', lambda x: x.abs().mean()),
                                       abs_trend6=('temp_trend_6h', lambda x: x.abs().mean())).round(3)
            h = hourly.join(hv)
            res['what_the_errors_track_hourly'] = {
                k: {'raw_MAE': round(float(h.raw_MAE.corr(h[k])), 3),
                    'cal_MAE': round(float(h.cal_MAE.corr(h[k])), 3)}
                for k in ['ssrd', 'humidity', 'wind', 'abs_dT', 'abs_trend6']}
            h.to_csv(os.path.join(OUT, 'error_by_hour.csv'))
            # the same for months, to place October
            mv = d.groupby('month').agg(ssrd=('ssrd', 'mean'), humidity=('humidity', 'mean'),
                                        wind=('wind_speed', 'mean'),
                                        abs_dT=('temp_change_1h', lambda x: x.abs().mean()),
                                        diurnal_range=('station temperature',
                                                       lambda x: x.groupby(d.loc[x.index, 'hour']).mean().max()
                                                       - x.groupby(d.loc[x.index, 'hour']).mean().min())).round(3)
            m = monthly.join(mv)
            res['what_the_errors_track_monthly'] = {
                k: {'raw_MAE': round(float(m.raw_MAE.corr(m[k])), 3),
                    'cal_MAE': round(float(m.cal_MAE.corr(m[k])), 3)}
                for k in ['ssrd', 'humidity', 'wind', 'abs_dT', 'diurnal_range']}
            res['october_context'] = {MONTH[i - 1]: mv.loc[i].to_dict() for i in [8, 9, 10, 11]}
            m.to_csv(os.path.join(OUT, 'error_by_month.csv'))

    json.dump(res, open(os.path.join(OUT, 'error_timing.json'), 'w'), indent=1, default=float)
    t = res['test_split']
    print('diurnal:', t['diurnal_peak'])
    print('seasonal:', t['seasonal_peak'], '| October:', t['october'])
    print('hourly correlations:', json.dumps(res['what_the_errors_track_hourly']))
    print('monthly correlations:', json.dumps(res['what_the_errors_track_monthly']))
    print('October context:', json.dumps(res['october_context']))
    print('LSO diurnal:', res['leave_sensors_out']['diurnal_peak'], res['leave_sensors_out']['seasonal_peak'])


if __name__ == '__main__':
    main()
