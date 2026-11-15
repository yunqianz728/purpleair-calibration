"""How much do the headline results move with the random partition and the model seed?

Table 2 rests on one 80/20 partition and one XGBoost seed (both 42). This repeats the final fit of the
models behind the paper's comparisons under five seeds: for each seed s the 80/20 partition is redrawn
with random_state=s, and the model is refitted on the new training rows with random_state=s and scored
on the new test rows. Hyperparameters are held at the values tuned for the main partition
(results50/models/*.json), so the spread reflects the data partition and the model's own randomness,
not a new search; seed 42 therefore reproduces Table 2 exactly, which the script checks.

Models (target: station temperature, as in Table 2):
  Temporal-National, Spatial-National,
  Temporal-ClimStrat (one model per climate zone, pooled over the same test rows),
  Temporal-TempStrat (one model per temperature class, pooled likewise).

Output: <PA_OUT>/seed_robustness.json  (resumable: finished seeds are kept)
Usage : PA_OUT=analysis_R1/results50 python3 analysis_R1/seed_robustness.py
"""
import json, os, sys, time
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rerun_models as R   # same data loader, feature sets and metrics as Table 2

SEEDS = [42, 1, 2, 3, 4]
TARGET = 'station temperature'
OUT = os.path.join(R.OUT, 'seed_robustness.json')
STRATS = {'ClimStrat': ('MainGroup', ['B_Arid', 'C_Temperate', 'D_Continental']),
          'TempStrat': ('Temperature class', ['Cold', 'Normal', 'Hot'])}


def params(name):
    return json.load(open(os.path.join(R.OUT, 'models', name + '.json')))['best_params']


def fit_predict(df, rows_tr, rows_te, feats, p, seed):
    m = xgb.XGBRegressor(**p, objective='reg:squarederror', tree_method='hist', random_state=seed, n_jobs=R.N_JOBS)
    m.fit(df.loc[rows_tr, feats], df.loc[rows_tr, TARGET], sample_weight=df.loc[rows_tr, 'Wsample'], verbose=False)
    return m.predict(df.loc[rows_te, feats])


def mae(y, p):
    return round(float(np.mean(np.abs(np.asarray(p) - np.asarray(y)))), 4)


def main():
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'seeds': {}}
    df = R.load(); R.log(f'seed_robustness: data {df.shape}')
    for s in SEEDS:
        if str(s) in res['seeds']:
            continue
        t0 = time.time()
        tr, te = train_test_split(df.index.values, test_size=0.2, random_state=s)
        y = df.loc[te, TARGET].values
        r = {}
        for ft in ['Temporal', 'Spatial']:
            r[f'{ft}-National'] = mae(y, fit_predict(df, tr, te, R.FEATURES[ft],
                                                    params(f'{ft}-National__station_temp__National'), s))
        for st, (col, vals) in STRATS.items():
            pred = np.full(len(te), np.nan)
            for v in vals:
                a = tr[(df.loc[tr, col] == v).values]; b = (df.loc[te, col] == v).values
                pred[b] = fit_predict(df, a, te[b], R.FEATURES['Temporal'],
                                      params(f'Temporal-{st}__station_temp__{v}'), s)
            r[f'Temporal-{st}'] = mae(y, pred)
        res['seeds'][str(s)] = r
        R.log(f'seed_robustness seed {s}: {r} | {round(time.time() - t0)}s')
        json.dump(res, open(OUT, 'w'), indent=1)

    S = res['seeds']; keys = list(next(iter(S.values())).keys())
    vals = {k: np.array([S[str(s)][k] for s in SEEDS]) for k in keys}
    nat = vals['Temporal-National']
    res['summary'] = {
        'MAE': {k: {'mean': round(float(v.mean()), 3), 'sd': round(float(v.std(ddof=1)), 3),
                    'min': round(float(v.min()), 3), 'max': round(float(v.max()), 3)} for k, v in vals.items()},
        'pct_vs_Temporal-National': {k: {'mean': round(float((100 * (vals[k] / nat - 1)).mean()), 1),
                                         'min': round(float((100 * (vals[k] / nat - 1)).min()), 1),
                                         'max': round(float((100 * (vals[k] / nat - 1)).max()), 1)}
                                     for k in ['Temporal-ClimStrat', 'Temporal-TempStrat']},
        'temporal_advantage_pct': {'mean': round(float((100 * (1 - nat / vals['Spatial-National'])).mean()), 1),
                                   'min': round(float((100 * (1 - nat / vals['Spatial-National'])).min()), 1),
                                   'max': round(float((100 * (1 - nat / vals['Spatial-National'])).max()), 1)},
        'climstrat_better_in_every_seed': bool((vals['Temporal-ClimStrat'] < nat).all()),
        'temporal_better_in_every_seed': bool((nat < vals['Spatial-National']).all()),
    }
    # seed 42 must reproduce the Table 2 figures
    t2 = json.load(open(os.path.join(R.OUT, 'models', 'Temporal-National__station_temp__National.json')))['test']['MAE']
    res['summary']['seed42_reproduces_table2'] = abs(S['42']['Temporal-National'] - t2) < 5e-4
    res['_note'] = __doc__.split('\n\n')[1].replace('\n', ' ')
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps(res['summary'], indent=1))


if __name__ == '__main__':
    main()
