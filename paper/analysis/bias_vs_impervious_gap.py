"""Does the raw warm bias grow with the sensor-station imperviousness gap? (Reviewer 1.5)

R1 asked whether the 5.4 C mean bias is inflated because the reference stations sit in less
built-up settings than the sensors. If that were the main cause, the bias should scale with how
much more impervious a sensor's surroundings are than its station's. This regresses each pair's
mean bias on that gap, over all hours and over night hours separately, and also reports the bias by
quartile of the gap so the reader can see the shape rather than only a slope.

The result is quoted in the fourth limitation of Section 5.4 and in the reply to R1.5.

Input : PA_PARQUET and <PA_OUT>/nlcd_points.csv (falls back to the default results directory,
        since NLCD imperviousness does not depend on the tuning budget)
Output: <PA_OUT>/bias_vs_impervious_gap.json
Usage : PA_PARQUET=... PA_OUT=analysis_R1/results50 python3 analysis_R1/bias_vs_impervious_gap.py
"""
import json, os
import numpy as np, pandas as pd
from scipy.stats import linregress

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
PARQUET = os.environ['PA_PARQUET']


def main():
    d = pd.read_parquet(PARQUET, columns=['sensor_id', 'hadisd_station_id', 'hour',
                                          'sensor temperature', 'station temperature'])
    d['bias'] = d['sensor temperature'] - d['station temperature']

    nlcd = os.path.join(BASE, 'nlcd_points.csv')
    if not os.path.exists(nlcd):
        nlcd = os.path.join(HERE, 'results', 'nlcd_points.csv')
    nl = pd.read_csv(nlcd, dtype={'id': str})
    nl = nl[nl.impervious_pct.between(0, 100)]          # drop the layer's NoData sentinels
    sen = nl[nl.kind == 'sensor'].set_index('id')['impervious_pct']
    sta = nl[nl.kind == 'station'].set_index('id')['impervious_pct']

    d['sid'] = d.sensor_id.astype(str)
    night = d['hour'].between(0, 5)
    g = (d.assign(_n=np.where(night, d.bias, np.nan))
           .groupby(['sid', 'hadisd_station_id'])
           .agg(bias_all=('bias', 'mean'), bias_night=('_n', 'mean'), n=('bias', 'size'))
           .reset_index())
    g['imp_sensor'] = g.sid.map(sen)
    g['imp_station'] = g.hadisd_station_id.map(sta)
    g = g.dropna(subset=['imp_sensor', 'imp_station'])
    g['gap'] = g.imp_sensor - g.imp_station

    out = {'n_pairs': int(len(g)), 'gap_median_pct_points': round(float(g.gap.median()), 1)}
    for lab, col in [('all hours', 'bias_all'), ('night 00-05', 'bias_night')]:
        r = linregress(g.gap, g[col])
        out[lab] = {'slope_C_per_10pp': round(float(r.slope * 10), 3),
                    'se_per_10pp': round(float(r.stderr * 10), 3),
                    'p': round(float(r.pvalue), 3), 'r': round(float(r.rvalue), 3),
                    'intercept_C': round(float(r.intercept), 2)}
    q = pd.qcut(g.gap, 4, labels=['Q1 smallest gap', 'Q2', 'Q3', 'Q4 largest gap'])
    out['by_quartile'] = {str(k): {'gap_median': round(float(g.gap[q == k].median()), 1),
                                   'bias_all': round(float(g.bias_all[q == k].mean()), 2),
                                   'bias_night': round(float(g.bias_night[q == k].mean()), 2),
                                   'n': int((q == k).sum())} for k in q.cat.categories}
    json.dump(out, open(os.path.join(BASE, 'bias_vs_impervious_gap.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
