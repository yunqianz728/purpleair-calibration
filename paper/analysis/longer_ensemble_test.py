"""Would more than 20,000 boosting rounds help? (SI Section S3)

Under the widened search the Temporal-National model stopped at 19,956 rounds, against a ceiling of
20,000, with a learning rate of 0.017; SI Section S3 says that a further small gain from longer
ensembles cannot be excluded. This measures it: the tuned hyperparameters are kept and the ceiling
raised to 40,000 rounds, with the same early stopping (100 rounds without improvement on the
validation set) and the same 64/16/20 partition as the tuning. If the validation optimum moves past
the old ceiling, the model is refitted on the 80% training rows with the new number of rounds and
scored on the test rows, against the 0.60 C of Table 2.

Output: <PA_OUT>/longer_ensemble_test.json
Usage : PA_PARQUET=paper/analysis/train.parquet PA_OUT=paper/results_wide PA_SEARCH=wide \
        python3 paper/analysis/longer_ensemble_test.py
"""
import json, os, time
import numpy as np, xgboost as xgb
from rerun_models import load, metrics, splits, FEATURES, OUT, SEED, N_JOBS

TARGET, CEILING, ES = 'station temperature', 40_000, 100


def main():
    df = load()
    feats = FEATURES['Temporal']
    rec = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))
    best = dict(rec['best_params'])
    old_rounds = int(best.pop('n_estimators'))
    tr, tr2, va, te = splits(df)
    X, y, w = df[feats], df[TARGET], df['Wsample']

    t0 = time.time()
    m = xgb.XGBRegressor(**best, n_estimators=CEILING, objective='reg:squarederror', eval_metric='mae',
                         tree_method='hist', early_stopping_rounds=ES, random_state=SEED, n_jobs=N_JOBS)
    m.fit(X.loc[tr2], y.loc[tr2], sample_weight=w.loc[tr2], eval_set=[(X.loc[va], y.loc[va])], verbose=False)
    curve = np.array(m.evals_result()['validation_0']['mae'])
    bi = int(m.best_iteration)
    at_old = float(curve[min(old_rounds, len(curve)) - 1])
    out = {'old_rounds': old_rounds, 'ceiling': CEILING, 'rounds_run': int(len(curve)),
           'best_rounds': bi + 1, 'stopped_early': bool(len(curve) < CEILING),
           'val_MAE_at_old_rounds': round(at_old, 5), 'val_MAE_at_best': round(float(curve[bi]), 5),
           'val_change_%': round(100 * (float(curve[bi]) / at_old - 1), 3),
           'seconds_search': round(time.time() - t0)}
    print(json.dumps(out, indent=1), flush=True)
    path = os.path.join(OUT, 'longer_ensemble_test.json')
    json.dump(out, open(path, 'w'), indent=1)

    if bi + 1 > old_rounds:
        t0 = time.time()
        f = xgb.XGBRegressor(**best, n_estimators=bi + 1, objective='reg:squarederror', tree_method='hist',
                             random_state=SEED, n_jobs=N_JOBS)
        f.fit(X.loc[tr], y.loc[tr], sample_weight=w.loc[tr], verbose=False)
        t = metrics(y.loc[te].values, f.predict(X.loc[te]))
        out['test_at_best_rounds'] = {k: round(v, 4) if isinstance(v, float) else v for k, v in t.items()}
        out['test_reference_MAE'] = round(rec['test']['MAE'], 4)
        out['test_change_%'] = round(100 * (t['MAE'] / rec['test']['MAE'] - 1), 2)
        out['seconds_refit'] = round(time.time() - t0)
        json.dump(out, open(path, 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
