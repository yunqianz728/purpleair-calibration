"""Build the corrected Table 2 (XGBoost, target station temperature) from results/models/*.json
and compare with the submitted Table 2. Writes results/table2_comparison.csv and .md."""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')   # PA_OUT selects the tuning budget
M = os.path.join(OUT, 'models')
J = lambda n: json.load(open(os.path.join(M, n + '.json')))
NAMES = {'Cold': 'Cold', 'Normal': 'Moderate', 'Hot': 'Hot', 'B_Arid': 'Arid', 'C_Temperate': 'Temperate', 'D_Continental': 'Continental'}
ORIG = {  # submitted Table 2: (MAE, RMSE, R2, vs Base %)
 ('Temporal-National', 'National'): (0.64, 0.87, 0.992, None), ('Temporal-National', 'Cold'): (0.61, 0.82, 0.987, None),
 ('Temporal-National', 'Moderate'): (0.65, 0.88, 0.986, None), ('Temporal-National', 'Hot'): (0.65, 0.90, 0.984, None),
 ('Spatial-National', 'National'): (0.81, 1.11, 0.987, None), ('Spatial-National', 'Cold'): (0.76, 1.03, 0.979, None),
 ('Spatial-National', 'Moderate'): (0.85, 1.15, 0.976, None), ('Spatial-National', 'Hot'): (0.80, 1.12, 0.975, None),
 ('Temporal-TempStrat', 'Cold'): (0.68, 0.95, 0.982, 12), ('Temporal-TempStrat', 'Moderate'): (0.77, 1.07, 0.979, 18),
 ('Temporal-TempStrat', 'Hot'): (0.80, 1.15, 0.974, 24),
 ('Spatial-TempStrat', 'Cold'): (0.68, 0.94, 0.983, -10), ('Spatial-TempStrat', 'Moderate'): (0.79, 1.08, 0.979, -7),
 ('Spatial-TempStrat', 'Hot'): (0.74, 1.03, 0.979, -9),
 ('Temporal-ClimStrat', 'Arid'): (0.90, 1.24, 0.986, 15), ('Temporal-ClimStrat', 'Temperate'): (0.69, 0.98, 0.984, 7),
 ('Temporal-ClimStrat', 'Continental'): (0.60, 0.84, 0.994, 3),
 ('Spatial-ClimStrat', 'Arid'): (1.20, 1.63, 0.976, 25), ('Spatial-ClimStrat', 'Temperate'): (0.91, 1.24, 0.975, 11),
 ('Spatial-ClimStrat', 'Continental'): (0.91, 1.25, 0.986, 21)}
rows = []
for ft in ['Temporal', 'Spatial']:
    nat = J(f'{ft}-National__station_temp__National')
    rows.append((f'{ft}-National', 'National', nat['test'], None))
    for k in ['Cold', 'Normal', 'Hot', 'B_Arid', 'C_Temperate', 'D_Continental']:
        rows.append((f'{ft}-National', NAMES[k], nat['by_stratum'][k], None))
    for st, keys in [('TempStrat', ['Cold', 'Normal', 'Hot']), ('ClimStrat', ['B_Arid', 'C_Temperate', 'D_Continental'])]:
        ms = [J(f'{ft}-{st}__station_temp__{k}')['test'] for k in keys]
        for k, m in zip(keys, ms):
            base = nat['by_stratum'][k]['MAE']
            rows.append((f'{ft}-{st}', NAMES[k], m, 100 * (m['MAE'] - base) / base))
        n = np.array([m['n'] for m in ms])   # pooled over strata = same test rows as the national model
        pooled = {'MAE': float(np.sum(n * [m['MAE'] for m in ms]) / n.sum()),
                  'RMSE': float(np.sqrt(np.sum(n * np.array([m['RMSE'] for m in ms]) ** 2) / n.sum())), 'R2': np.nan, 'n': int(n.sum())}
        rows.append((f'{ft}-{st}', 'Pooled', pooled, 100 * (pooled['MAE'] - nat['test']['MAE']) / nat['test']['MAE']))
out = []
for cfg, s, m, vs in rows:
    o = ORIG.get((cfg, s), (None,) * 4)
    out.append({'config': cfg, 'stratum': s, 'n_test': m['n'], 'MAE': round(m['MAE'], 3), 'RMSE': round(m['RMSE'], 3),
                'R2': round(m['R2'], 4) if m['R2'] == m['R2'] else None, 'vs_base_%': None if vs is None else round(vs, 1),
                'orig_MAE': o[0], 'orig_RMSE': o[1], 'orig_R2': o[2], 'orig_vs_base_%': o[3]})
df = pd.DataFrame(out)
df.to_csv(os.path.join(OUT, 'table2_comparison.csv'), index=False)
open(os.path.join(OUT, 'table2_comparison.md'), 'w').write(df.to_markdown(index=False))
print(df.to_string(index=False))
tn, sn = J('Temporal-National__station_temp__National')['test'], J('Spatial-National__station_temp__National')['test']
print(f"\nTemporal vs Spatial national: {100*(tn['MAE']-sn['MAE'])/sn['MAE']:.1f}% MAE")
raw = 5.417  # placeholder check below uses data
