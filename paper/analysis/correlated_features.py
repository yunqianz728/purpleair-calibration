"""Reviewer 2, Section 5.2: correlated features, model size, and what that means for SHAP (R1).

R2's point has two halves, and this script answers each with a number:
  (a) "the low model error depends on ... multiple correlated features (essentially overfitting)"
      -> cluster the 63 Temporal features at |r| >= 0.9 (7 clusters covering 33 features, computed in
         feature_correlation.py), keep ONE representative per cluster -> 37 effectively distinct
         features, re-tune and re-fit under the same protocol as the main run, and compare. Also a
         feature-count curve (top-k by gain importance, k = 5, 10, 20, 37, 63) showing how much of the
         accuracy the small contributions actually carry.
  (b) "with multiple correlated features ... interpretation of relative importance is less meaningful"
      -> recompute TreeSHAP for the Figure-5 models (Temporal-TempStrat, target temp_error) and
         aggregate |SHAP| BY CLUSTER, so importance that correlated features split among themselves is
         reported once, at group level.

Representatives are the highest-gain member of each cluster in the fitted full model (documented in
the output). Evaluation uses the main run's fixed 80/20 split, so numbers are comparable to Table 2.
The feature-count curve reuses the full model's hyperparameters (noted as such); the 37-feature model
is re-tuned properly.
Usage: python3 analysis_R1/correlated_features.py
"""
import json, os, time
import numpy as np, pandas as pd, optuna, xgboost as xgb
from rerun_models import load, metrics, FEATURES, OUT, SEED, N_JOBS, N_TRIALS, splits, log, tune_and_fit

CF = os.path.join(OUT, 'correlated_features'); os.makedirs(CF, exist_ok=True)
FEATS = FEATURES['Temporal']
TARGET = 'station temperature'
CLUSTERS = json.load(open(os.path.join(OUT, 'feature_clusters_r_ge_0.9.json')))
optuna.logging.set_verbosity(optuna.logging.WARNING)


def gain(model_path, feats):
    b = xgb.Booster(); b.load_model(model_path)
    b.feature_names = list(feats)
    g = b.get_score(importance_type='gain')
    return {f: float(g.get(f, 0.0)) for f in feats}


def cluster_map(feats):
    """feature -> cluster label; singletons keep their own name."""
    m = {}
    for i, c in enumerate(CLUSTERS):
        for f in c:
            if f in feats:
                m[f] = f'cluster{i + 1}'
    for f in feats:
        m.setdefault(f, f)
    return m


def main():
    df = load(); log(f'correlated_features: data {df.shape}')
    tr, tr2, va, te = splits(df)
    y = df[TARGET]
    full_json = json.load(open(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.json')))
    g = gain(os.path.join(OUT, 'models', 'Temporal-National__station_temp__National.ubj'), FEATS)
    reps, dropped = [], []
    for c in CLUSTERS:
        mem = [f for f in c if f in FEATS]
        if not mem:
            continue
        r = max(mem, key=lambda f: g[f]); reps.append(r); dropped += [f for f in mem if f != r]
    reduced = [f for f in FEATS if f not in dropped]
    log(f'clusters: {len(CLUSTERS)}, representatives {reps}, reduced set {len(reduced)} features')
    out = {'clusters': CLUSTERS, 'representatives': reps, 'dropped': dropped,
           'n_full': len(FEATS), 'n_reduced': len(reduced),
           'full_model': {'test': full_json['test'], 'train': full_json['train']}}

    # (a1) 37-feature model, properly re-tuned
    p37 = os.path.join(CF, 'reduced37.json')
    if os.path.exists(p37):
        out['reduced37'] = json.load(open(p37))
    else:
        t0 = time.time()
        model, best, trials = tune_and_fit(df.loc[tr2, reduced], y.loc[tr2], df.loc[tr2, 'Wsample'],
                                           df.loc[va, reduced], y.loc[va].values,
                                           df.loc[tr, reduced], y.loc[tr], df.loc[tr, 'Wsample'])
        res = {'n_features': len(reduced), 'features': reduced,
               'test': metrics(y.loc[te].values, model.predict(df.loc[te, reduced])),
               'train': metrics(y.loc[tr].values, model.predict(df.loc[tr, reduced])),
               'best_params': best, 'trials': trials, 'seconds': round(time.time() - t0)}
        json.dump(res, open(p37, 'w'), indent=1); out['reduced37'] = res
        model.save_model(os.path.join(CF, 'reduced37.ubj'))
        log(f"reduced37: test MAE {res['test']['MAE']:.3f} vs full {full_json['test']['MAE']:.3f} | {res['seconds']}s")

    # (a2) feature-count curve, full model's hyperparameters held fixed
    pcurve = os.path.join(CF, 'feature_count_curve.json')
    if os.path.exists(pcurve):
        out['curve'] = json.load(open(pcurve))
    else:
        order = sorted(FEATS, key=lambda f: -g[f])
        curve = []
        for k in [5, 10, 20, 37, 63]:
            sel = order[:k]
            m = xgb.XGBRegressor(**full_json['best_params'], objective='reg:squarederror',
                                 tree_method='hist', random_state=SEED, n_jobs=N_JOBS)
            m.fit(df.loc[tr, sel], y.loc[tr], sample_weight=df.loc[tr, 'Wsample'], verbose=False)
            mt = metrics(y.loc[te].values, m.predict(df.loc[te, sel]))
            curve.append({'k': k, 'features': sel, **{kk: mt[kk] for kk in ['MAE', 'RMSE', 'R2']}})
            log(f"curve k={k}: MAE {mt['MAE']:.3f} RMSE {mt['RMSE']:.3f}")
        json.dump(curve, open(pcurve, 'w'), indent=1); out['curve'] = curve

    # (b) cluster-aggregated SHAP for the Figure-5 models
    pshap = os.path.join(CF, 'cluster_shap.json')
    if os.path.exists(pshap):
        out['cluster_shap'] = json.load(open(pshap))
    else:
        cmap = cluster_map(FEATS)
        rng = np.random.default_rng(SEED)
        shap_out = {}
        for stratum in ['Cold', 'Normal', 'Hot']:
            name = f'Temporal-TempStrat__temp_error__{stratum}'
            b = xgb.Booster(); b.load_model(os.path.join(OUT, 'models', name + '.ubj'))
            b.feature_names = list(FEATS)
            ite = te[(df.loc[te, 'Temperature class'] == stratum).values]
            ite = rng.choice(ite, size=min(20000, len(ite)), replace=False)
            contrib = b.predict(xgb.DMatrix(df.loc[ite, FEATS], feature_names=list(FEATS)), pred_contribs=True)
            mabs = np.abs(contrib[:, :-1]).mean(axis=0)
            per_feature = dict(zip(FEATS, mabs.round(5).tolist()))
            byc = {}
            for f, v in per_feature.items():
                byc[cmap[f]] = byc.get(cmap[f], 0.0) + v
            tot = sum(byc.values())
            shap_out[stratum] = {
                'n_rows': int(len(ite)),
                'per_feature_top15': dict(sorted(per_feature.items(), key=lambda x: -x[1])[:15]),
                'by_cluster_top15': {k: round(v, 5) for k, v in sorted(byc.items(), key=lambda x: -x[1])[:15]},
                'by_cluster_share_%': {k: round(100 * v / tot, 1) for k, v in sorted(byc.items(), key=lambda x: -x[1])[:10]}}
            log(f'cluster SHAP {stratum}: top groups ' +
                ', '.join(f'{k} {v}%' for k, v in list(shap_out[stratum]['by_cluster_share_%'].items())[:4]))
        json.dump(shap_out, open(pshap, 'w'), indent=1); out['cluster_shap'] = shap_out

    json.dump({k: v for k, v in out.items() if k != 'clusters'} | {'clusters': CLUSTERS},
              open(os.path.join(CF, 'summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
