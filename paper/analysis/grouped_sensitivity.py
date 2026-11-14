"""Leave-sensors-out sensitivity: does the Temporal-National model generalise better to unseen sensors
when features that let it memorise individual sites are removed? Same 5 GroupKFold folds and tuned params."""
import json, os, numpy as np, pandas as pd, xgboost as xgb
from sklearn.model_selection import GroupKFold
from rerun_models import load, metrics, FEATURES, OUT, SEED, N_JOBS, log
SITE = ['sensor_lat', 'sensor_lon', 'elevation_sensor', 'sensor_tcc']
VARIANTS = {'no_site_ids': SITE, 'no_site_ids_no_life_year': SITE + ['life', 'year', 'temp_life_interaction_sensor']}
df = load(); y = df['station temperature'].values
best = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))['best_params']
out = {}
for name, drop in VARIANTS.items():
    feats = [f for f in FEATURES['Temporal'] if f not in drop]
    pred = np.full(len(df), np.nan)
    for k, (a, b) in enumerate(GroupKFold(n_splits=5).split(df, groups=df['sensor_id'])):
        m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
        m.fit(df.iloc[a][feats], y[a], sample_weight=df.iloc[a]['Wsample'], verbose=False)
        pred[b] = m.predict(df.iloc[b][feats])
    ps = pd.Series(np.abs(pred - y)).groupby(df['sensor_id'].values).mean()
    out[name] = {'dropped': drop, 'n_features': len(feats), 'overall': metrics(y, pred),
                 'per_sensor_MAE_median': float(ps.median())}
    log(f'grouped_sensitivity {name}: MAE {out[name]["overall"]["MAE"]:.3f}, per-sensor median {ps.median():.3f}')
json.dump(out, open(os.path.join(OUT, 'grouped_sensitivity.json'), 'w'), indent=1)
