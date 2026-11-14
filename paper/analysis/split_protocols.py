"""How the train/test split defines the deployment scenario (R1, Temporal features, target T_station).

Four protocols are reported in the revision; this script adds the two middle ones. All of them use
the same 63 Temporal features, which are strictly backward-looking (lags, rolling means, trends),
so no feature uses information after the time it is evaluated at. What differs is which ROWS, with
their reference-station labels, are available for training:

  1. random rows        (rerun_models.py main)     -> retrospective gap filling: the same sensor's
                        MAE 0.724                     neighbouring hours, before AND after, are labelled.
  2. blocked by week    (here, 'week')             -> same sensors, whole weeks held out: removes the
                                                      hour-to-hour adjacency but keeps the season mix.
  3. chronological      (here, 'chrono')           -> real-time operation: for each sensor, train on the
                        per sensor                    earliest 80 % of ITS OWN record, test on the latest
                                                      20 %. No label from after the evaluated hour.
  4. leave-sensors-out  (rerun_models.py grouped)  -> a new sensor with no reference pairing at all.
                        MAE 1.900

Hyperparameters are re-tuned inside each protocol with a validation split of the SAME kind (held-out
training weeks / the latest fifth of the training period), so tuning never sees the test rows and
targets the error the protocol measures. Optuna TPE, seed 42, 50 trials, each trial fitted on a random
third of the inner-training rows for speed; final model refit on all training rows.
Usage: python3 analysis_R1/split_protocols.py
"""
import json, os, time
import numpy as np, pandas as pd, optuna, xgboost as xgb
from rerun_models import load, metrics, FEATURES, OUT, SEED, N_JOBS, N_TRIALS, log

SP = os.path.join(OUT, 'split_protocols'); os.makedirs(SP, exist_ok=True)
FEATS = FEATURES['Temporal']
TARGET = 'station temperature'
optuna.logging.set_verbosity(optuna.logging.WARNING)


def tune(X, y, w, itr, iva, rng):
    itr = rng.choice(itr, size=max(len(itr) // 3, 1), replace=False)
    Xtr, ytr, wtr, Xva, yva = X.iloc[itr], y[itr], w[itr], X.iloc[iva], y[iva]
    trials = []

    def objective(trial):
        p = dict(learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                 max_depth=trial.suggest_int('max_depth', 3, 10),
                 n_estimators=trial.suggest_int('n_estimators', 100, 1000),
                 subsample=trial.suggest_float('subsample', 0.5, 1.0),
                 colsample_bytree=trial.suggest_float('colsample_bytree', 0.5, 1.0),
                 reg_alpha=trial.suggest_float('reg_alpha', 0, 10),
                 reg_lambda=trial.suggest_float('reg_lambda', 0, 10),
                 min_child_weight=trial.suggest_int('min_child_weight', 1, 10))
        m = xgb.XGBRegressor(**p, objective='reg:squarederror', eval_metric='mae', tree_method='hist',
                             early_stopping_rounds=50, random_state=SEED, n_jobs=N_JOBS)
        m.fit(Xtr, ytr, sample_weight=wtr, eval_set=[(Xva, yva)], verbose=False)
        v = float(np.mean(np.abs(m.predict(Xva) - yva)))
        trial.set_user_attr('best_iteration', int(m.best_iteration))
        trials.append({'trial': trial.number, 'val_MAE': v, 'best_iteration': int(m.best_iteration), **p})
        return v

    study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=SEED))
    study.optimize(objective, n_trials=N_TRIALS)
    best = dict(study.best_params)
    best['n_estimators'] = study.best_trial.user_attrs['best_iteration'] + 1
    return best, trials


def week_split(df, rng):
    """Whole ISO weeks assigned 80/20; inner validation = 20 % of the training weeks."""
    wk = pd.to_datetime(df['datetime']).dt.strftime('%G-%V').values
    weeks = np.array(sorted(set(wk))); rng.shuffle(weeks)
    n_te = int(round(0.2 * len(weeks)))
    te_w, tr_w = set(weeks[:n_te]), weeks[n_te:]
    n_va = int(round(0.2 * len(tr_w))); va_w = set(tr_w[:n_va])
    in_te = np.isin(wk, list(te_w)); in_va = np.isin(wk, list(va_w))
    idx = np.arange(len(df))
    return idx[~in_te], idx[~in_te & ~in_va], idx[in_va], idx[in_te], {'n_weeks': len(weeks), 'n_test_weeks': n_te}


def chrono_split(df):
    """Per sensor: earliest 80 % of its own record trains, latest 20 % tests;
    inner validation = the latest fifth of each sensor's training period."""
    t = pd.to_datetime(df['datetime'])
    r = t.groupby(df['sensor_id']).rank(pct=True, method='first').values
    idx = np.arange(len(df))
    te = idx[r > 0.8]; tr = idx[r <= 0.8]
    va = idx[(r > 0.64) & (r <= 0.8)]; tr2 = idx[r <= 0.64]
    return tr, tr2, va, te, {'rule': 'per-sensor time rank: train <=0.8, inner-train <=0.64, val 0.64-0.8'}


def main():
    df = load(); log(f'split_protocols: data {df.shape}')
    X = df[FEATS]; y = df[TARGET].values; w = df['Wsample'].values
    out = {}
    for proto in ['week', 'chrono']:
        jpath = os.path.join(SP, f'{proto}.json')
        if os.path.exists(jpath):
            out[proto] = json.load(open(jpath)); log(f'skip {proto}'); continue
        rng = np.random.default_rng(SEED)
        tr, tr2, va, te, info = week_split(df, rng) if proto == 'week' else chrono_split(df)
        t0 = time.time()
        best, trials = tune(X, y, w, tr2, va, rng)
        m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
        m.fit(X.iloc[tr], y[tr], sample_weight=w[tr], verbose=False)
        p = m.predict(X.iloc[te])
        ps = pd.Series(np.abs(p - y[te])).groupby(df['sensor_id'].values[te]).mean()
        bias = pd.Series(p - y[te]).groupby(df['sensor_id'].values[te]).mean()
        res = {'protocol': proto, 'split': info, 'n_train': int(len(tr)), 'n_test': int(len(te)),
               'test': metrics(y[te], p), 'train': metrics(y[tr], m.predict(X.iloc[tr])),
               'per_sensor_MAE_q': ps.quantile([0.1, 0.5, 0.9]).round(3).to_dict(),
               'per_sensor_abs_bias_median': float(bias.abs().median()),
               'by_zone': {z: metrics(y[te][(df.MainGroup.values[te] == z)], p[(df.MainGroup.values[te] == z)])
                           for z in ['B_Arid', 'C_Temperate', 'D_Continental']},
               'by_class': {c: metrics(y[te][(df['Temperature class'].values[te] == c)], p[(df['Temperature class'].values[te] == c)])
                            for c in ['Cold', 'Normal', 'Hot']},
               'best_params': best, 'trials': trials, 'seconds': round(time.time() - t0)}
        json.dump(res, open(jpath, 'w'), indent=1)
        pd.DataFrame({'row': te, 'pred': p}).to_parquet(os.path.join(SP, f'pred_{proto}.parquet'))
        out[proto] = res
        log(f"{proto}: test MAE {res['test']['MAE']:.3f} RMSE {res['test']['RMSE']:.3f} R2 {res['test']['R2']:.4f} "
            f"| per-sensor median {res['per_sensor_MAE_q'][0.5]:.3f} |bias| {res['per_sensor_abs_bias_median']:.3f} "
            f"| depth {best['max_depth']} | {res['seconds']}s")
    json.dump({k: {k2: v[k2] for k2 in v if k2 != 'trials'} for k, v in out.items()},
              open(os.path.join(SP, 'summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
