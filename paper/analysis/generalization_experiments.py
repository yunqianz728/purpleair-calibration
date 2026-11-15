"""Experiments to improve the Temporal-National model on UNSEEN sensors (leave-sensors-out), R1.

Outer evaluation: the same 5-fold GroupKFold by sensor as rerun_models.py `grouped`.
Three factors, crossed (4 variants):
  * tuning     : hyperparameters re-tuned INSIDE each outer fold with a sensor-grouped validation split
                 (GroupShuffleSplit, 20 % of the training sensors), so tuning targets new-sensor error
                 and never sees the outer test sensors (nested);
  * features   : 'full' (63 Temporal features) or 'reduced' (drops site-identifying and deployment-time
                 features: sensor_lat, sensor_lon, elevation_sensor, sensor_tcc, life, year,
                 temp_life_interaction_sensor);
  * sensor QC  : 'all' sensors or 'qc' = training excludes sensors failing an a-priori raw-data rule:
                 correlation of daily-mean sensor vs station temperature < 0.8 (sensor does not track
                 ambient temperature -> malfunction, indoor placement or wrong pairing). The rule uses raw
                 data only (never model errors). Flagged sensors are still predicted and reported apart.
Tuning: Optuna TPE (seed 42), 20 trials, same search space as the main run; for speed each trial is fitted
on a random third of the inner-training rows (hourly rows are strongly autocorrelated); early stopping
on the grouped validation sensors; final model refit on all outer-training rows.
Usage: python3 analysis_R1/generalization_experiments.py
"""
import json, os, time
import numpy as np, pandas as pd, optuna, xgboost as xgb
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from rerun_models import load, metrics, FEATURES, OUT, SEED, N_JOBS, N_TRIALS, log, MAX_DEPTH, MAX_TREES, ES_ROUNDS, WIDE

EXP = os.path.join(OUT, 'generalization'); os.makedirs(EXP, exist_ok=True)
DROP = ['sensor_lat', 'sensor_lon', 'elevation_sensor', 'sensor_tcc', 'life', 'year', 'temp_life_interaction_sensor']
FEATSETS = {'full': FEATURES['Temporal'], 'reduced': [f for f in FEATURES['Temporal'] if f not in DROP]}
VARIANTS = [('full', 'all'), ('reduced', 'all'), ('full', 'qc'), ('reduced', 'qc')]
QC_R_DAILY = 0.8
TARGET = 'station temperature'
optuna.logging.set_verbosity(optuna.logging.WARNING)


def qc_flags(df):
    d = df[['sensor_id', 'sensor temperature', 'station temperature']].copy()
    d['date'] = pd.to_datetime(df['datetime']).dt.date
    dm = d.groupby(['sensor_id', 'date'])[['sensor temperature', 'station temperature']].mean().reset_index()
    r = dm.groupby('sensor_id')[['sensor temperature', 'station temperature']].apply(
        lambda x: np.corrcoef(x['sensor temperature'], x['station temperature'])[0, 1])
    flagged = sorted(r[r < QC_R_DAILY].index.tolist())
    return flagged, r


def tune(X, y, w, groups, rng):
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    itr, iva = next(gss.split(X, groups=groups))
    itr = rng.choice(itr, size=len(itr) // 3, replace=False)
    Xtr, ytr, wtr, Xva, yva = X.iloc[itr], y[itr], w[itr], X.iloc[iva], y[iva]
    trials = []

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


def main():
    df = load(); log(f'generalization: data {df.shape}')
    flagged, r_daily = qc_flags(df)
    is_flag = df['sensor_id'].isin(flagged).values
    json.dump({'rule': f'daily-mean correlation sensor vs station < {QC_R_DAILY}', 'flagged_sensors': [int(s) for s in flagged],
               'n_rows_flagged': int(is_flag.sum()), 'r_daily': {int(k): round(float(v), 3) for k, v in r_daily.items()}},
              open(os.path.join(EXP, 'qc_flags.json'), 'w'), indent=1)
    log(f'QC: {len(flagged)} sensors flagged ({is_flag.sum()} rows): {flagged}')
    y = df[TARGET].values; w = df['Wsample'].values; groups = df['sensor_id'].values
    folds = list(GroupKFold(n_splits=5).split(df, groups=groups))
    summary = {}
    # PA_JOB=<i> (1-20) runs one variant x fold only, for cluster arrays; a final run without it assembles the summary.
    job = int(os.environ.get('PA_JOB', 0))
    for vi, (fs, qc) in enumerate(VARIANTS):
        name = f'{fs}_{qc}'; feats = FEATSETS[fs]; X = df[feats]
        pred = np.full(len(df), np.nan); fold_info = []
        for k, (a, b) in enumerate(folds):
            fpath = os.path.join(EXP, f'{name}_fold{k}.json')
            ppath = os.path.join(EXP, f'{name}_fold{k}_pred.npy')
            if job and job != vi * 5 + k + 1:
                continue
            if os.path.exists(fpath):
                fold_info.append(json.load(open(fpath))); pred[b] = np.load(ppath); continue
            t0 = time.time()
            if qc == 'qc':
                a = a[~is_flag[a]]
            rng = np.random.default_rng(SEED + k)
            best, trials = tune(X.iloc[a], y[a], w[a], groups[a], rng)
            m = xgb.XGBRegressor(**best, objective='reg:squarederror', tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
            m.fit(X.iloc[a], y[a], sample_weight=w[a], verbose=False)
            pred[b] = m.predict(X.iloc[b]); np.save(ppath, pred[b])
            info = {'fold': k, 'best_params': best, 'trials': trials, 'seconds': round(time.time() - t0),
                    'test_all': metrics(y[b], pred[b]), 'test_retained': metrics(y[b][~is_flag[b]], pred[b][~is_flag[b]])}
            json.dump(info, open(fpath, 'w'), indent=1); fold_info.append(info)
            log(f'{name} fold {k}: MAE all {info["test_all"]["MAE"]:.3f} retained {info["test_retained"]["MAE"]:.3f} '
                f'depth {best["max_depth"]} lr {best["learning_rate"]:.3f} trees {best["n_estimators"]} | {info["seconds"]}s')
        if job:
            continue
        ps = pd.Series(np.abs(pred - y)).groupby(groups).mean()
        keep = ~is_flag
        summary[name] = {'features': fs, 'qc': qc, 'n_features': len(feats),
                         'all_sensors': metrics(y, pred), 'retained_sensors': metrics(y[keep], pred[keep]),
                         'flagged_sensors': metrics(y[is_flag], pred[is_flag]),
                         'per_sensor_MAE_retained_q': ps[~ps.index.isin(flagged)].quantile([0.1, 0.5, 0.9]).round(3).to_dict(),
                         'by_zone_retained': {z: metrics(y[keep & (df.MainGroup == z).values], pred[keep & (df.MainGroup == z).values])
                                              for z in ['B_Arid', 'C_Temperate', 'D_Continental']},
                         'folds': [{k2: f[k2] for k2 in ['fold', 'best_params', 'seconds', 'test_all', 'test_retained']} for f in fold_info]}
        pd.DataFrame({'pred': pred}).to_parquet(os.path.join(EXP, f'pred_{name}.parquet'))
        log(f'{name}: MAE all {summary[name]["all_sensors"]["MAE"]:.3f} retained {summary[name]["retained_sensors"]["MAE"]:.3f}')
        json.dump(summary, open(os.path.join(EXP, 'summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
