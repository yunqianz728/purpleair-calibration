"""How much does the model depend on the ERA5 inputs, which arrive about five days late?

The paper quotes 1.08 C for real-time operation (the chronological protocol of SI Section S7), but
that model uses ERA5 and ERA5-Land variables, which are published about five days behind real time,
so a strictly real-time pipeline would have to run without them or with a forecast substitute. This
refits the Temporal-National model with every reanalysis-derived predictor removed, leaving only what
the sensor itself and the clock provide, and reports the change in error:

  random rows      Table 2's partition, with the hyperparameters tuned there   (reference 0.60 C)
  chronological    SI Table S12's partition, with the hyperparameters tuned there (reference 1.08 C)

Each reference is refitted here with the same hyperparameters and all 63 features, so that the two
fits of a pair differ only in the feature set.

Output: <PA_OUT>/no_reanalysis_test.json
Usage : PA_PARQUET=paper/analysis/train.parquet PA_OUT=paper/results_wide PA_SEARCH=wide \
        python3 paper/analysis/no_reanalysis_test.py
"""
import json, os, time
import numpy as np, xgboost as xgb
from rerun_models import load, metrics, splits, FEATURES, OUT, SEED, N_JOBS
from split_protocols import chrono_split

TARGET = 'station temperature'
# every predictor computed from ERA5 or ERA5-Land (SI Table S3): radiation, heat flux, precipitation, wind
REANALYSIS = ['ssrd', 'ssrd_1h_ago', 'ssrd_2h_ago', 'ssrd_change', 'ssrd_sum_3h', 'ssrd_sum_6h', 'diurnal_radiation',
              'strd', 'sshf', 'tp', 'u10', 'v10', 'wind_speed', 'wind_direction']


def fit_score(df, feats, params, tr, te):
    t0 = time.time()
    m = xgb.XGBRegressor(**params, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
    m.fit(df.iloc[tr][feats], df.iloc[tr][TARGET], sample_weight=df.iloc[tr]['Wsample'], verbose=False)
    r = metrics(df.iloc[te][TARGET].values, m.predict(df.iloc[te][feats]))
    r['seconds'] = round(time.time() - t0)
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}


def main():
    df = load().reset_index(drop=True)
    full = FEATURES['Temporal']
    missing = [f for f in REANALYSIS if f not in full]
    assert not missing, f'not in the feature set: {missing}'
    sensor_only = [f for f in full if f not in REANALYSIS]
    out = {'n_features': {'all': len(full), 'without_reanalysis': len(sensor_only)}, 'removed': REANALYSIS}
    path = os.path.join(OUT, 'no_reanalysis_test.json')

    rnd = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))['best_params']
    tr, _, _, te = splits(df)
    pos = df.index.get_indexer
    chrono = json.load(open(os.path.join(OUT, 'split_protocols', 'chrono.json')))['best_params']
    ctr, _, _, cte, _ = chrono_split(df)
    for proto, params, a, b in [('random', rnd, pos(tr), pos(te)), ('chronological', chrono, ctr, cte)]:
        out[proto] = {}
        for name, feats in [('all_features', full), ('without_reanalysis', sensor_only)]:
            out[proto][name] = fit_score(df, feats, params, a, b)
            print(f'{proto} {name}: {out[proto][name]}', flush=True)
            json.dump(out, open(path, 'w'), indent=1)
        f, s = out[proto]['all_features']['MAE'], out[proto]['without_reanalysis']['MAE']
        out[proto]['change_%'] = round(100 * (s / f - 1), 1)
    json.dump(out, open(path, 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
