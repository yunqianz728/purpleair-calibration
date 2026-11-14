"""Per-feature SHAP means for the Temporal-TempStrat models, used by SI Tables S6 and S7.

The pooled top-25 rankings of Tables S6 and S7 are computed on a larger sample than the 2,000 rows
Figure 5 is drawn from, because a ranking of 63 features is noisier than six group totals. This
script produces that larger computation. It exists separately from scripts/figures/generate_figure5.py
so that the figure keeps its own, smaller sample and neither has to compromise for the other; the
sample size each uses is stated where its numbers appear in the SI.

(This file restores a computation that was previously embedded in a hand-written figure script. When
that script was dropped in favour of the original plotting code, SI Tables S6 and S7 were briefly
left depending on a JSON file that nothing in the repository could regenerate.)

Input : PA_PARQUET, and <PA_OUT>/models/Temporal-TempStrat__{target}__{stratum}.ubj
Output: <PA_OUT>/figures/figure5_groups.json and figure_s2_groups.json
Usage : PA_PARQUET=... PA_OUT=analysis_R1/results50 python3 analysis_R1/shap_export.py
"""
import json, os
import numpy as np, pandas as pd, xgboost as xgb
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
FIG = os.path.join(BASE, 'figures'); os.makedirs(FIG, exist_ok=True)
PARQUET = os.environ['PA_PARQUET']
FEATS = json.load(open(os.path.join(HERE, 'feature_sets.json')))['TEMPORAL_FEATURES']
SEED, N_ROWS, TOPN = 42, 10000, 10
# One generator is drawn from in a fixed stratum order, so the output is reproducible as written;
# it is not independent of that order, which is why the order is pinned in the loop below.

GROUPS = json.load(open(os.path.join(HERE, 'feature_groups.json'))) if \
    os.path.exists(os.path.join(HERE, 'feature_groups.json')) else None
if GROUPS is None:                       # single source of truth: the grouping the figure script uses
    src = open(os.path.join(HERE, '..', 'scripts', 'figures', 'generate_figure5.py'), encoding='utf-8').read()
    ns = {}
    exec(src[src.index('FEATURE_GROUPS'):src.index('# ====', src.index('FEATURE_GROUPS'))], ns)
    GROUPS = ns['FEATURE_GROUPS']


def main():
    cols = sorted(set(FEATS) | {'Temperature class'})
    df = pd.read_parquet(PARQUET, columns=cols)
    _, te = train_test_split(df.index.values, test_size=0.2, random_state=SEED)
    test = df.loc[te]
    rng = np.random.default_rng(SEED)

    for target, name in [('temp_error', 'figure5_groups.json'),
                         ('station_temp', 'figure_s2_groups.json')]:
        out = {}
        for stratum in ['Cold', 'Normal', 'Hot']:
            m = xgb.XGBRegressor()
            m.load_model(os.path.join(BASE, 'models', f'Temporal-TempStrat__{target}__{stratum}.ubj'))
            d = test[test['Temperature class'] == stratum]
            X = d.iloc[rng.choice(len(d), size=min(N_ROWS, len(d)), replace=False)][FEATS]
            contrib = m.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[:, :-1]
            mean_abs = pd.Series(np.abs(contrib).mean(axis=0), index=FEATS)
            signed = pd.Series(contrib.mean(axis=0), index=FEATS)
            top = list(mean_abs.sort_values(ascending=False).head(TOPN).index)
            shares = {g: float(mean_abs[[f for f in fs if f in mean_abs.index]].sum())
                      for g, fs in GROUPS.items()}
            tot = sum(shares.values())
            out[stratum] = {
                'group_pct': {g: round(100 * v / tot, 1) for g, v in shares.items()},
                'top_features': [(f, round(float(mean_abs[f]), 4)) for f in top],
                'feature_pct': (100 * mean_abs / mean_abs.sum()).round(2).sort_values(ascending=False).to_dict(),
                'feature_mean_abs': mean_abs.round(5).to_dict(),
                'feature_mean_signed': signed.round(5).to_dict(),
                'n_rows_pie': int(len(X)), 'n_rows_beeswarm': 0}
            print(f'  {target} {stratum}: {len(X)} rows', flush=True)
        json.dump(out, open(os.path.join(FIG, name), 'w'), indent=1)
        print(f'wrote {os.path.join(FIG, name)}')


if __name__ == '__main__':
    main()
