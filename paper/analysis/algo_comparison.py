"""The algorithm comparison under the protocol and search range of the main results (SI Table S5).

SI Table S5 comes from the original four-algorithm comparison (20 Optuna trials, the original search
ranges, and a partition that was not common to every configuration; see its provenance note), while
XGBoost has since been re-tuned under the protocol of Section 3.5 with the widened search of SI
Section S3. This puts LightGBM and CatBoost on the same footing for the two unstratified
configurations behind the choice of algorithm: the same 64/16/20 partition and sample weights,
50 trials of the seeded TPE sampler, early stopping after 100 rounds on the validation set, and
search ranges widened in the same way as for XGBoost (up to 20,000 rounds sampled log-uniformly, and
larger trees: LightGBM up to 1,023 leaves, CatBoost depth up to 12). RandomForest, excluded from the
main analysis for its much higher error, is not refitted.

Each run is one configuration x target x algorithm (8 in all); PA_ONLY=<name> selects one, so a
cluster array can run them in parallel. Searches resume from their journal after a time limit.

Output: <PA_OUT>/algo_comparison/<name>.json   (test metrics, best parameters, trial history)
Usage : PA_PARQUET=... PA_OUT=... PA_ONLY=Temporal-National__station_temp__LightGBM python3 algo_comparison.py
        python3 algo_comparison.py --list
"""
import json, os, sys, time
import numpy as np, optuna
from rerun_models import load, metrics, splits, FEATURES, OUT, SEED, N_JOBS, N_TRIALS, log

TARGETS = {'station_temp': 'station temperature', 'temp_error': 'temp_error'}
ES, MAX_ROUNDS = 100, 20000
GPU = os.environ.get('PA_DEVICE', '') == 'cuda'
NAMES = [f'{fs}-National__{tk}__{algo}' for fs in ['Temporal', 'Spatial'] for tk in TARGETS
         for algo in ['LightGBM', 'CatBoost']]
D = os.path.join(OUT, 'algo_comparison')
optuna.logging.set_verbosity(optuna.logging.WARNING)


def make(algo, p, n_rounds=None, es=True):
    if algo == 'LightGBM':
        import lightgbm as lgb
        kw = dict(objective='regression', metric='mae', boosting_type='gbdt', random_state=SEED, n_jobs=N_JOBS,
                  verbose=-1, n_estimators=n_rounds or p['n_estimators'],
                  **{k: v for k, v in p.items() if k != 'n_estimators'})
        return lgb.LGBMRegressor(**kw)
    from catboost import CatBoostRegressor
    kw = dict(loss_function='MAE', random_seed=SEED, verbose=False, iterations=n_rounds or p['iterations'],
              thread_count=N_JOBS, **{k: v for k, v in p.items() if k != 'iterations'})
    if es:
        kw['early_stopping_rounds'] = ES
    if GPU:   # MAE is the 0.5 quantile; the GPU implementation takes it in that form
        kw.update(task_type='GPU', loss_function='Quantile:alpha=0.5', eval_metric='MAE')
    return CatBoostRegressor(**kw)


def space(algo, trial):
    if algo == 'LightGBM':
        return dict(n_estimators=trial.suggest_int('n_estimators', 100, MAX_ROUNDS, log=True),
                    num_leaves=trial.suggest_int('num_leaves', 20, 1023, log=True),
                    learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    subsample=trial.suggest_float('subsample', 0.5, 1.0), subsample_freq=1,
                    colsample_bytree=trial.suggest_float('colsample_bytree', 0.5, 1.0),
                    reg_alpha=trial.suggest_float('reg_alpha', 0, 10),
                    reg_lambda=trial.suggest_float('reg_lambda', 0, 10),
                    min_child_weight=trial.suggest_int('min_child_weight', 1, 10))
    return dict(iterations=trial.suggest_int('iterations', 100, MAX_ROUNDS, log=True),
                depth=trial.suggest_int('depth', 4, 12),
                learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                l2_leaf_reg=trial.suggest_float('l2_leaf_reg', 1, 10),
                bagging_temperature=trial.suggest_float('bagging_temperature', 0.0, 1.0),
                random_strength=trial.suggest_float('random_strength', 0.0, 10.0))


def run(name, df):
    fs, tk, algo = name.split('__')[0].split('-')[0], name.split('__')[1], name.split('__')[2]
    feats, target = FEATURES[fs], TARGETS[tk]
    tr, tr2, va, te = splits(df)
    X, y, w = df[feats], df[target], df['Wsample']

    def fit(model, rows, eval_rows=None):
        if eval_rows is None:
            model.fit(X.loc[rows], y.loc[rows], sample_weight=w.loc[rows])
        elif algo == 'LightGBM':
            import lightgbm as lgb
            model.fit(X.loc[rows], y.loc[rows], sample_weight=w.loc[rows], eval_set=[(X.loc[eval_rows], y.loc[eval_rows])],
                      callbacks=[lgb.early_stopping(ES, verbose=False)])
        else:
            model.fit(X.loc[rows], y.loc[rows], sample_weight=w.loc[rows], eval_set=(X.loc[eval_rows], y.loc[eval_rows]))
        return model

    def best_iter(m):
        return int(m.best_iteration_ if algo == 'LightGBM' else m.get_best_iteration()) + (0 if algo == 'LightGBM' else 1)

    def objective(trial):
        m = fit(make(algo, space(algo, trial)), tr2, va)
        trial.set_user_attr('best_iteration', best_iter(m))
        return float(np.mean(np.abs(m.predict(X.loc[va]) - y.loc[va].values)))   # unweighted, as for XGBoost

    from optuna.storages import JournalStorage
    from optuna.storages.journal import JournalFileBackend
    os.makedirs(os.path.join(D, 'studies'), exist_ok=True)
    st = optuna.create_study(study_name=name, direction='minimize', load_if_exists=True,
                             storage=JournalStorage(JournalFileBackend(os.path.join(D, 'studies', name + '.log'))),
                             sampler=optuna.samplers.TPESampler(seed=SEED))
    done = [t for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if done:
        st.sampler = optuna.samplers.TPESampler(seed=SEED + 1000 + len(done))
    t0 = time.time()
    st.optimize(objective, n_trials=max(0, N_TRIALS - len(done)),
                callbacks=[lambda s, t: log(f'{name} trial {len(s.trials)}: val {t.value} ({time.time() - t0:.0f}s)')])
    best = dict(st.best_params)
    rounds = st.best_trial.user_attrs['best_iteration']
    if algo == 'LightGBM':
        best['n_estimators'] = rounds
    else:
        best['iterations'] = rounds
    fixed = {'subsample_freq': 1} if algo == 'LightGBM' else {}
    m = fit(make(algo, {**best, **fixed}, es=False), tr)
    res = {'name': name, 'algorithm': algo, 'features': fs, 'target': tk, 'n_features': len(feats),
           'test': metrics(y.loc[te].values, m.predict(X.loc[te])), 'best_params': best,
           'trials': [{'trial': t.number, 'val_MAE': t.value, 'best_iteration': t.user_attrs.get('best_iteration'), **t.params}
                      for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE],
           'seconds': round(time.time() - t0)}
    json.dump(res, open(os.path.join(D, name + '.json'), 'w'), indent=1)
    log(f"{name}: test MAE {res['test']['MAE']:.4f} RMSE {res['test']['RMSE']:.4f}")


def main():
    if '--list' in sys.argv:
        print('\n'.join(NAMES)); return
    only = [x for x in os.environ.get('PA_ONLY', '').split(',') if x] or NAMES
    os.makedirs(D, exist_ok=True)
    df = load()
    if os.environ.get('PA_SMOKE'):        # a quick end-to-end check on a small sample
        global MAX_ROUNDS
        df = df.sample(20000, random_state=0); MAX_ROUNDS = 300
    for name in only:
        if os.path.exists(os.path.join(D, name + '.json')):
            log(f'skip {name}: done'); continue
        run(name, df)


if __name__ == '__main__':
    main()
