"""How the tuned XGBoost models sit in their search space, before and after it was widened.

Under the original space (depth 3-10, 100-1,000 boosting rounds) every one of the 28 configurations
chose the deepest trees allowed and most ended near the ceiling on rounds, so the optimum lay at the
edge of the range. This script records that, does the same for the widened run (depth 3-14, up to
20,000 rounds), and compares test MAE configuration by configuration. SI Section S3 quotes
its output.

The number of rounds recorded for a model is the one it was refitted with: the best validation
iteration of the winning trial, plus one (rerun_models.tune_and_fit).

Usage: python3 paper/analysis/search_space_summary.py [--old paper/results_50trials] [--new paper/results_wide]
Writes <new>/search_space_summary.json.
"""
import argparse, glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load(folder):
    out = {}
    for f in sorted(glob.glob(os.path.join(folder, 'models', '*.json'))):
        j = json.load(open(f))
        if 'best_params' in j:
            out[os.path.basename(f)[:-5]] = j
    return out


def describe(models, max_depth, max_trees):
    d = np.array([m['best_params']['max_depth'] for m in models.values()])
    t = np.array([m['best_params']['n_estimators'] for m in models.values()])
    return {'n_configs': len(models), 'depth_ceiling': max_depth, 'trees_ceiling': max_trees,
            'n_at_depth_ceiling': int((d == max_depth).sum()),
            'depth_counts': {int(k): int(v) for k, v in zip(*np.unique(d, return_counts=True))},
            'n_trees_ge_90pct_of_ceiling': int((t >= 0.9 * max_trees).sum()),
            'trees_median': float(np.median(t)), 'trees_min': int(t.min()), 'trees_max': int(t.max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--old', default=os.path.join(HERE, '..', 'results_50trials'))
    ap.add_argument('--new', default=os.path.join(HERE, '..', 'results_wide'))
    a = ap.parse_args()
    old, new = load(a.old), load(a.new)
    res = {'original': describe(old, 10, 1000)}
    if new:
        res['widened'] = describe(new, 14, 20000)
        both = sorted(set(old) & set(new))
        ch = {k: 100 * (new[k]['test']['MAE'] / old[k]['test']['MAE'] - 1) for k in both}
        v = np.array(list(ch.values()))
        res['test_MAE_change_pct'] = {'n_configs': len(both), 'n_improved': int((v < 0).sum()),
                                      'mean': float(v.mean()), 'min': float(v.min()), 'max': float(v.max()),
                                      'by_config': ch}
        if len(both) < len(old):
            res['missing_in_new'] = sorted(set(old) - set(new))
    os.makedirs(a.new, exist_ok=True)
    json.dump(res, open(os.path.join(a.new, 'search_space_summary.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'test_MAE_change_pct'}, indent=1))
    if 'test_MAE_change_pct' in res:
        print({k: v for k, v in res['test_MAE_change_pct'].items() if k != 'by_config'})


if __name__ == '__main__':
    main()
