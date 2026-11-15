"""Per-sensor test MAE for the national model, by climate zone.

Section 4.2 quotes the median of these by zone (Continental / Temperate / Arid) and the count of
sensors above 1.0 C, and Figure 4(b) is the same distribution drawn as boxplots. The numbers were
first produced inline while drafting; this script exists so they can be regenerated and so the
Data Availability statement's claim that the evaluation code is provided is true of them too.

Input : PA_PARQUET and <PA_OUT>/pred_Temporal-National__station_temp__National.parquet
Output: <PA_OUT>/per_sensor_mae.csv
Usage : PA_PARQUET=... PA_OUT=analysis_R1/results50 python3 analysis_R1/per_sensor_mae.py
"""
import os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
PARQUET = os.environ['PA_PARQUET']


def main():
    df = pd.read_parquet(PARQUET, columns=['sensor_id', 'station temperature', 'MainGroup'])
    p = pd.read_parquet(os.path.join(BASE, 'pred_Temporal-National__station_temp__National.parquet'))
    d = df.loc[p['row'].values].copy()
    # unweighted, matching Table 2 and Section 4.2; Figure 4 uses the same convention
    d['ae'] = np.abs(p['pred'].values - d['station temperature'].values)
    s = d.groupby(['MainGroup', 'sensor_id'])['ae'].agg(['mean', 'size']).reset_index()
    s.to_csv(os.path.join(BASE, 'per_sensor_mae.csv'), index=False)

    by = s.groupby('MainGroup')['mean'].agg(['count', 'median', 'mean', 'min', 'max']).round(3)
    print(by.to_string())
    print(f"\nsensors above 1.0 C: {int((s['mean'] > 1.0).sum())} of {len(s)}")
    for z, g in s.groupby('MainGroup'):
        q = g['mean'].quantile([.25, .75]).round(3).tolist()
        print(f'  {z:15s} interquartile {q[0]}-{q[1]}  (>1.0 C: {int((g["mean"] > 1.0).sum())} of {len(g)})')


if __name__ == '__main__':
    main()
