"""Fit and score every XGBoost configuration in the paper under one evaluation protocol.

Protocol (identical for every configuration and target):
  * one global 80/20 train/test split of all 797,744 rows (random_state=42);
    stratified models use the rows of the SAME split that fall in their stratum,
    so national and stratified models are scored on identical test rows;
  * hyperparameters tuned with Optuna (TPE, seed 42, 20 trials) on a validation
    subset (20 %) of the training rows only; early stopping on that validation subset;
  * final model refit on all training rows with the best parameters; the test set is
    touched exactly once, for scoring; sample weights (Wsample) used for training only;
  * metrics unweighted (as in the manuscript); every Optuna trial is saved.

Usage:
  python3 analysis_R1/rerun_models.py main      # 14 configurations x 2 targets
  python3 analysis_R1/rerun_models.py grouped   # 5-fold leave-sensors-out test of the national models
"""
import json, os, sys, time
import numpy as np, pandas as pd, optuna, xgboost as xgb
from sklearn.model_selection import train_test_split, GroupKFold

HERE = os.path.dirname(os.path.abspath(__file__))
# PA_OUT / PA_N_TRIALS let a larger tuning budget be run into its own folder without touching the
# 20-trial results, so the two budgets can be compared (SI: was 20 trials enough?).
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
os.makedirs(os.path.join(OUT, 'models'), exist_ok=True)
PARQUET = os.environ.get('PA_PARQUET', '')
CSV = os.path.join(HERE, '..', 'data', 'training_data_with_classification.csv.gz')
FEATS = json.load(open(os.path.join(HERE, 'feature_sets.json')))
FEATURES = {'Temporal': FEATS['TEMPORAL_FEATURES'], 'Spatial': FEATS['SPATIAL_FEATURES']}
TARGETS = {'station temperature': 'station_temp', 'temp_error': 'temp_error'}
SEED, N_TRIALS = 42, int(os.environ.get('PA_N_TRIALS', 20))
N_JOBS = int(os.environ.get('PA_N_JOBS', 8))
# PA_SEARCH=wide widens the XGBoost search: depth up to 14, up to 20,000 trees (sampled on a log scale)
# and early stopping after 100 rounds. In the default space, every 50-trial search ended at the depth
# limit (10) and most near the tree limit (1,000), so the default results are capped by the space.
WIDE = os.environ.get('PA_SEARCH', '') == 'wide'
MAX_DEPTH, MAX_TREES, ES_ROUNDS = (14, 20000, 100) if WIDE else (10, 1000, 50)
# PA_ONLY=<name>[,<name>...] runs only the named configurations (e.g. one per cluster job).
ONLY = [x for x in os.environ.get('PA_ONLY', '').split(',') if x]
# PA_DEVICE=cuda trains every XGBoost model on a GPU (same 'hist' algorithm). It is applied by replacing
# xgb.XGBRegressor, so the scripts that import this module use the same device without changes.
DEVICE = os.environ.get('PA_DEVICE', '')
if DEVICE:
    class _XGBRegressorOnDevice(xgb.XGBRegressor):
        def __init__(self, **kw):
            kw.setdefault('device', DEVICE)
            super().__init__(**kw)
    xgb.XGBRegressor = _XGBRegressorOnDevice
optuna.logging.set_verbosity(optuna.logging.WARNING)

STRATA = [('National', None, None)] + \
         [('TempStrat', 'Temperature class', s) for s in ['Cold', 'Normal', 'Hot']] + \
         [('ClimStrat', 'MainGroup', z) for z in ['B_Arid', 'C_Temperate', 'D_Continental']]
CONFIGS = [(f, st, col, val) for f in ['Temporal', 'Spatial'] for (st, col, val) in STRATA]


def log(msg):
    line = time.strftime('%Y-%m-%d %H:%M:%S ') + msg
    print(line, flush=True)
    with open(os.path.join(OUT, 'rerun.log'), 'a') as f:
        f.write(line + '\n')


def load():
    if PARQUET and os.path.exists(PARQUET):
        return pd.read_parquet(PARQUET)
    return pd.read_csv(CSV, low_memory=False)


def metrics(y, p):
    e = np.asarray(p) - np.asarray(y)
    return {'MAE': float(np.mean(np.abs(e))), 'RMSE': float(np.sqrt(np.mean(e ** 2))),
            'R2': float(1 - np.sum(e ** 2) / np.sum((np.asarray(y) - np.mean(y)) ** 2)),
            'bias': float(np.mean(e)), 'n': int(len(e))}


def splits(df):
    idx = df.index.values
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED)
    tr2, va = train_test_split(tr, test_size=0.2, random_state=SEED)
    return tr, tr2, va, te


def run_study(objective, name=None):
    """Run the Optuna search. Under PA_SEARCH=wide every finished trial is also written to
    <OUT>/studies/<name>.log and logged, so a job stopped by a time limit resumes from the trials it
    had finished instead of starting over. Sampling is unchanged: the same seeded TPE sampler, and an
    uninterrupted run gives the same trials as before. Returns the study and the trial records."""
    sampler = optuna.samplers.TPESampler(seed=SEED)
    if WIDE and name:
        from optuna.storages import JournalStorage
        from optuna.storages.journal import JournalFileBackend
        os.makedirs(os.path.join(OUT, 'studies'), exist_ok=True)
        storage = JournalStorage(JournalFileBackend(os.path.join(OUT, 'studies', name + '.log')))
        study = optuna.create_study(study_name=name, storage=storage, load_if_exists=True,
                                    direction='minimize', sampler=sampler)
    else:
        study = optuna.create_study(direction='minimize', sampler=sampler)
    done = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    t0 = [time.time()]

    def progress(st, t):
        if name and t.state == optuna.trial.TrialState.COMPLETE:
            n = len([x for x in st.trials if x.state == optuna.trial.TrialState.COMPLETE])
            log(f"trial {name} {n}/{N_TRIALS}: val {t.value:.4f} depth {t.params['max_depth']} "
                f"lr {t.params['learning_rate']:.3f} trees {t.user_attrs['best_iteration'] + 1} | {time.time() - t0[0]:.0f}s")
        t0[0] = time.time()

    if done:
        # a fresh sampler with the original seed would repeat the first random draws, so a resumed search
        # continues with a seed derived from the number of trials already done
        study.sampler = optuna.samplers.TPESampler(seed=SEED + 1000 + len(done))
        log(f'resume {name}: {len(done)} of {N_TRIALS} trials already done')
    study.optimize(objective, n_trials=max(0, N_TRIALS - len(done)), callbacks=[progress])
    trials = [{'trial': t.number, 'val_MAE': t.value, 'best_iteration': t.user_attrs['best_iteration'], **t.params}
              for t in sorted(study.trials, key=lambda t: t.number) if t.state == optuna.trial.TrialState.COMPLETE]
    return study, trials


def tune_and_fit(X_tr2, y_tr2, w_tr2, X_va, y_va, X_tr, y_tr, w_tr, name=None):

    def objective(trial):
        p = dict(learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                 max_depth=trial.suggest_int('max_depth', 3, MAX_DEPTH),
                 n_estimators=trial.suggest_int('n_estimators', 100, MAX_TREES, log=WIDE),
                 subsample=trial.suggest_float('subsample', 0.5, 1.0),
                 colsample_bytree=trial.suggest_float('colsample_bytree', 0.5, 1.0),
                 reg_alpha=trial.suggest_float('reg_alpha', 0, 10),
                 reg_lambda=trial.suggest_float('reg_lambda', 0, 10),
                 min_child_weight=trial.suggest_int('min_child_weight', 1, 10))
        m = xgb.XGBRegressor(**p, objective='reg:squarederror', eval_metric='mae', tree_method='hist',
                             early_stopping_rounds=ES_ROUNDS, random_state=SEED, n_jobs=N_JOBS)
        m.fit(X_tr2, y_tr2, sample_weight=w_tr2, eval_set=[(X_va, y_va)], verbose=False)
        val_mae = float(np.mean(np.abs(m.predict(X_va) - y_va)))   # unweighted validation MAE
        trial.set_user_attr('best_iteration', int(m.best_iteration))
        return val_mae

    study, trials = run_study(objective, name)
    best = dict(study.best_params)
    best['n_estimators'] = study.best_trial.user_attrs['best_iteration'] + 1
    model = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist',
                             random_state=SEED, n_jobs=N_JOBS)
    model.fit(X_tr, y_tr, sample_weight=w_tr, verbose=False)
    return model, best, trials


def run_main():
    df = load(); log(f'data {df.shape}')
    tr, tr2, va, te = splits(df)
    pd.Series(te).to_csv(os.path.join(OUT, 'test_index.csv'), index=False)
    for feat_type, strat_type, col, val in CONFIGS:
        for target, tshort in TARGETS.items():
            stratum = val or 'National'
            name = f'{feat_type}-{strat_type}__{tshort}__{stratum}'
            jpath = os.path.join(OUT, 'models', name + '.json')
            if ONLY and name not in ONLY:
                continue
            if os.path.exists(jpath):
                log(f'skip {name} (done)'); continue
            feats = FEATURES[feat_type]
            sel = (lambda ix: ix) if col is None else (lambda ix, c=col, v=val: ix[(df.loc[ix, c] == v).values])
            i_tr, i_tr2, i_va, i_te = sel(tr), sel(tr2), sel(va), sel(te)
            t0 = time.time()
            model, best, trials = tune_and_fit(df.loc[i_tr2, feats], df.loc[i_tr2, target], df.loc[i_tr2, 'Wsample'],
                                               df.loc[i_va, feats], df.loc[i_va, target].values,
                                               df.loc[i_tr, feats], df.loc[i_tr, target], df.loc[i_tr, 'Wsample'], name=name)
            p_te = model.predict(df.loc[i_te, feats]); p_tr = model.predict(df.loc[i_tr, feats])
            res = {'config': f'{feat_type}-{strat_type}', 'feature_type': feat_type, 'stratification': strat_type,
                   'stratum': stratum, 'target': target, 'n_features': len(feats),
                   'n_train': int(len(i_tr)), 'n_test': int(len(i_te)),
                   'test': metrics(df.loc[i_te, target].values, p_te),
                   'train': metrics(df.loc[i_tr, target].values, p_tr),
                   'best_params': best, 'trials': trials, 'seconds': round(time.time() - t0)}
            if col is None:   # national model: also score every stratum on the same test rows
                y = df.loc[i_te, target].values
                res['by_stratum'] = {}
                for c2, v2 in [('Temperature class', s) for s in ['Cold', 'Normal', 'Hot']] + \
                              [('MainGroup', z) for z in ['B_Arid', 'C_Temperate', 'D_Continental']]:
                    mask = (df.loc[i_te, c2] == v2).values
                    res['by_stratum'][v2] = metrics(y[mask], p_te[mask])
                pd.DataFrame({'row': i_te, 'pred': p_te}).to_parquet(os.path.join(OUT, f'pred_{name}.parquet'))
            model.save_model(os.path.join(OUT, 'models', name + '.ubj'))
            json.dump(res, open(jpath, 'w'), indent=1)
            log(f"done {name}: test MAE {res['test']['MAE']:.3f} RMSE {res['test']['RMSE']:.3f} "
                f"R2 {res['test']['R2']:.4f} | train MAE {res['train']['MAE']:.3f} | {res['seconds']}s")


def run_grouped():
    """Leave-sensors-out: 5-fold GroupKFold by sensor, national models, tuned params from the main run."""
    df = load(); log(f'grouped: data {df.shape}')
    target = 'station temperature'
    out = {}
    for feat_type in ['Temporal', 'Spatial']:
        name = f'{feat_type}-National__station_temp__National'
        best = json.load(open(os.path.join(OUT, 'models', name + '.json')))['best_params']
        feats = FEATURES[feat_type]
        preds = pd.Series(np.nan, index=df.index)
        folds = []
        for k, (a, b) in enumerate(GroupKFold(n_splits=5).split(df, groups=df['sensor_id'])):
            m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
            m.fit(df.iloc[a][feats], df.iloc[a][target], sample_weight=df.iloc[a]['Wsample'], verbose=False)
            p = m.predict(df.iloc[b][feats]); preds.iloc[b] = p
            folds.append({'fold': k, 'n_sensors': int(df.iloc[b]['sensor_id'].nunique()),
                          **metrics(df.iloc[b][target].values, p)})
            log(f'grouped {feat_type} fold {k}: MAE {folds[-1]["MAE"]:.3f}')
        y = df[target].values
        per_sensor = pd.DataFrame({'sensor': df['sensor_id'], 'ae': np.abs(preds.values - y)}).groupby('sensor').ae.mean()
        out[feat_type] = {'overall': metrics(y, preds.values), 'folds': folds,
                          'by_zone': {z: metrics(y[(df.MainGroup == z).values], preds.values[(df.MainGroup == z).values])
                                      for z in ['B_Arid', 'C_Temperate', 'D_Continental']},
                          'per_sensor_MAE_quantiles': per_sensor.quantile([0.1, 0.5, 0.9]).round(3).to_dict()}
        pd.DataFrame({'pred': preds.values}).to_parquet(os.path.join(OUT, f'pred_grouped_{feat_type}.parquet'))
        log(f'grouped {feat_type}: overall MAE {out[feat_type]["overall"]["MAE"]:.3f}')
    json.dump(out, open(os.path.join(OUT, 'grouped_cv.json'), 'w'), indent=1)


def run_grouped_strat():
    """Leave-sensors-out for the stratified Temporal models (same 5 sensor folds as run_grouped):
    in each fold one model per stratum is trained on the training sensors' rows of that stratum
    (tuned params from the main run) and predicts the held-out sensors' rows of that stratum."""
    df = load(); log(f'grouped_strat: data {df.shape}')
    target = 'station temperature'
    feats = FEATURES['Temporal']
    y = df[target].values
    out = {}
    for strat_type, col, vals in [('TempStrat', 'Temperature class', ['Cold', 'Normal', 'Hot']),
                                  ('ClimStrat', 'MainGroup', ['B_Arid', 'C_Temperate', 'D_Continental'])]:
        params = {v: json.load(open(os.path.join(OUT, 'models', f'Temporal-{strat_type}__station_temp__{v}.json')))['best_params']
                  for v in vals}
        preds = np.full(len(df), np.nan)
        for k, (a, b) in enumerate(GroupKFold(n_splits=5).split(df, groups=df['sensor_id'])):
            for v in vals:
                ia = a[(df[col].values[a] == v)]; ib = b[(df[col].values[b] == v)]
                if len(ib) == 0:
                    continue
                m = xgb.XGBRegressor(**params[v], objective='reg:squarederror', tree_method='hist',
                                     random_state=SEED, n_jobs=N_JOBS)
                m.fit(df.iloc[ia][feats], df.iloc[ia][target], sample_weight=df.iloc[ia]['Wsample'], verbose=False)
                preds[ib] = m.predict(df.iloc[ib][feats])
            log(f'grouped_strat Temporal-{strat_type} fold {k}: MAE {np.nanmean(np.abs(preds[b] - y[b])):.3f}')
        out[f'Temporal-{strat_type}'] = {'overall': metrics(y, preds),
                                         'by_stratum': {v: metrics(y[(df[c2] == v).values], preds[(df[c2] == v).values])
                                                        for c2, v in [('Temperature class', s) for s in ['Cold', 'Normal', 'Hot']] +
                                                        [('MainGroup', z) for z in ['B_Arid', 'C_Temperate', 'D_Continental']]}}
        pd.DataFrame({'pred': preds}).to_parquet(os.path.join(OUT, f'pred_grouped_Temporal-{strat_type}.parquet'))
        log(f'grouped_strat Temporal-{strat_type}: overall MAE {out[f"Temporal-{strat_type}"]["overall"]["MAE"]:.3f}')
    json.dump(out, open(os.path.join(OUT, 'grouped_cv_strat.json'), 'w'), indent=1)


if __name__ == '__main__':
    {'main': run_main, 'grouped': run_grouped, 'grouped_strat': run_grouped_strat}[sys.argv[1]]()
