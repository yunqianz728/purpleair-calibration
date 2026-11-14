"""20 vs 50 Optuna trials: did the larger search budget change any conclusion? (SI)

The 20-trial run left 16 of 28 configurations with their best score on the final trial, and the
imbalance was lopsided (12 of 14 Spatial against 4 of 14 Temporal), which could have inflated the
Temporal-over-Spatial advantage. This compares the two budgets model by model and recomputes the
headline contrasts under each.
"""
import json, glob, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
A, B = os.path.join(HERE, 'results'), os.path.join(HERE, 'results50')


def load(d):
    out = {}
    for f in glob.glob(os.path.join(d, 'models', '*.json')):
        r = json.load(open(f))
        t = sorted(r['trials'], key=lambda x: x['trial'])
        v = np.array([x['val_MAE'] for x in t])
        out[os.path.basename(f)[:-5]] = {
            'MAE': r['test']['MAE'], 'RMSE': r['test']['RMSE'], 'R2': r['test']['R2'],
            'train_MAE': r['train']['MAE'], 'feature_type': r['feature_type'],
            'n_trials': len(v), 'best_trial': int(np.argmin(v)) + 1,
            'last5_spread': float(np.ptp(np.minimum.accumulate(v)[-5:])),
            'by_stratum': r.get('by_stratum')}
    return out


a, b = load(A), load(B)
rows = [{'model': k, 'MAE_20': a[k]['MAE'], 'MAE_50': b[k]['MAE'],
         'delta_%': 100 * (b[k]['MAE'] - a[k]['MAE']) / a[k]['MAE'],
         'best_trial_20': a[k]['best_trial'], 'best_trial_50': b[k]['best_trial'],
         'feature_type': a[k]['feature_type']}
        for k in sorted(set(a) & set(b))]
df = pd.DataFrame(rows).round(3)
df.to_csv(os.path.join(HERE, 'results50', 'budget_comparison.csv'), index=False)
print(df.to_string(index=False))

print('\n--- convergence ---')
for lbl, d in (('20 trials', a), ('50 trials', b)):
    n = len(d); last = sum(1 for v in d.values() if v['best_trial'] > v['n_trials'] - 5)
    final = sum(1 for v in d.values() if v['best_trial'] == v['n_trials'])
    moving = sum(1 for v in d.values() if v['last5_spread'] > 0.01)
    sp = sum(1 for v in d.values() if v['feature_type'] == 'Spatial' and v['best_trial'] == v['n_trials'])
    tp = sum(1 for v in d.values() if v['feature_type'] == 'Temporal' and v['best_trial'] == v['n_trials'])
    print(f'{lbl}: best on final trial {final}/{n} (Spatial {sp}/14, Temporal {tp}/14); '
          f'best within last 5 {last}/{n}; best-so-far still moving >0.01C over last 5: {moving}/{n}')

print('\n--- headline contrasts ---')
for lbl, d in (('20 trials', a), ('50 trials', b)):
    t = d['Temporal-National__station_temp__National']['MAE']
    s = d['Spatial-National__station_temp__National']['MAE']
    print(f'{lbl}: Temporal-National {t:.3f}, Spatial-National {s:.3f}, '
          f'temporal advantage {100*(t-s)/s:+.1f}%')
print('\nmean |change| from 20 -> 50 trials: %.1f%%; max improvement %.1f%%, max worsening %+.1f%%'
      % (df['delta_%'].abs().mean(), df['delta_%'].min(), df['delta_%'].max()))
