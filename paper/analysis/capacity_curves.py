"""Validation error against the number of boosting rounds, national model against stratified models.

A controlled experiment behind the SI figure on model capacity: every model gets the same
hyperparameters and differs only in the rows it is trained on, so the curves show how the value of
stratification changes as the ensemble grows, separately from anything the tuning chose. The
hyperparameters are those tuned for the Temporal-National model in the original search (subsample,
column sampling, regularization, minimum child weight), with depth 12 and learning rate 0.05 so that
the curve is still moving at the original ceiling of 1,000 rounds, and 20,000 rounds with no early
stopping so that the whole curve is recorded.

Only training and validation rows are used (the 64/16 part of the 64/16/20 split); test rows are not
touched. Each stratified model is scored on the validation rows in its stratum; because the strata
partition those rows, the pooled stratified curve covers exactly the rows of the national curve.

Usage: PA_PARQUET=paper/analysis/train.parquet PA_OUT=paper/results_wide python3 paper/analysis/capacity_curves.py
Writes <PA_OUT>/capacity_curves.json, one stratum at a time, and resumes from it if stopped.
"""
import json, os, time
import pandas as pd
import xgboost as xgb
import rerun_models as R

PARAMS = dict(subsample=0.7536, colsample_bytree=0.9407, reg_alpha=9.644, reg_lambda=8.150,
              min_child_weight=3, max_depth=12, learning_rate=0.05, n_estimators=20000)
FEATURES, TARGET = 'Temporal', 'station temperature'


def main():
    out = os.path.join(R.OUT, 'capacity_curves.json')
    res = json.load(open(out)) if os.path.exists(out) else {}
    res['_setup'] = dict(params=PARAMS, features=FEATURES, target=TARGET, seed=R.SEED,
                         scored_on='validation rows (16% of data)')
    df = R.load(); R.log(f'capacity_curves: data {df.shape}')
    F = R.FEATURES[FEATURES]
    tr, tr2, va, te = R.splits(df)
    for st, col, val in R.STRATA:
        key = 'National' if st == 'National' else f'{st}:{val}'
        if key in res:
            continue
        a = tr2 if col is None else tr2[df.loc[tr2, col].values == val]
        v = va if col is None else va[df.loc[va, col].values == val]
        t = time.time()
        m = xgb.XGBRegressor(**PARAMS, objective='reg:squarederror', eval_metric='mae', tree_method='hist',
                             random_state=R.SEED, n_jobs=R.N_JOBS)
        m.fit(df.loc[a, F], df.loc[a, TARGET], sample_weight=df.loc[a, 'Wsample'],
              eval_set=[(df.loc[v, F], df.loc[v, TARGET])], verbose=False)
        curve = m.evals_result()['validation_0']['mae']
        res[key] = dict(n_val=int(len(v)), n_train=int(len(a)), curve=[round(x, 5) for x in curve],
                        seconds=round(time.time() - t))
        json.dump(res, open(out, 'w'))
        R.log(f'capacity {key}: val MAE {curve[999]:.4f} at 1,000 rounds, {curve[-1]:.4f} at {len(curve):,}')


if __name__ == '__main__':
    main()
