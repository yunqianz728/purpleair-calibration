"""Replacement for SI Figure S1: the ACTUAL Bayesian-optimisation histories (R1).

The submitted Figure S1 was produced by `generate_realistic_convergence()` in
notebooks/PA_final_modified.ipynb (cell 5), which draws a curve from a target MAE with an exponential
decay plus Gaussian noise. It is a simulation, not an optimisation record, and the numbers quoted in
its caption are outputs of that simulation.

This script plots the real Optuna trial histories recorded by analysis_R1/rerun_models.py, which saves
every trial of every model (`trials` in results/models/*.json). Panel (a) keeps the structure of the
old figure -- one configuration in detail -- and panel (b) compares the three climate zones. Both show
per-trial validation MAE and the running best.

Output: analysis_R1/results/figures/figureS1_convergence_real.{png,pdf} and a JSON of the numbers that
the new caption must quote.
Usage: python3 analysis_R1/make_figure_s1.py
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')   # PA_OUT selects the tuning budget
M = os.path.join(BASE, 'models')
FIG = os.path.join(BASE, 'figures'); os.makedirs(FIG, exist_ok=True)
CONFIG = 'Spatial-ClimStrat__station_temp__'          # same configuration as the old figure
ZONES = [('D_Continental', 'Continental'), ('B_Arid', 'Arid'), ('C_Temperate', 'Temperate')]
COLORS = {'Continental': '#1f77b4', 'Arid': '#d62728', 'Temperate': '#2ca02c'}

plt.rcParams.update({'font.family': 'Arial', 'font.size': 13, 'axes.unicode_minus': False,
                     'mathtext.fontset': 'stix', 'mathtext.default': 'regular'})


def history(zone):
    t = json.load(open(os.path.join(M, CONFIG + zone + '.json')))['trials']
    t = sorted(t, key=lambda x: x['trial'])
    v = np.array([x['val_MAE'] for x in t])
    return np.arange(1, len(v) + 1), v, np.minimum.accumulate(v)


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    caption = {}

    # (a) one configuration in detail
    x, v, b = history('D_Continental')
    ax = axes[0]
    ax.plot(x, v, 'o-', color='#999999', lw=1.2, ms=5, label='Trial validation MAE', zorder=2)
    ax.plot(x, b, '-', color=COLORS['Continental'], lw=2.4, label='Best so far', zorder=3)
    k = int(np.argmin(v))
    ax.plot(x[k], v[k], '*', color='#d62728', ms=20, zorder=4,
            label=f'Best: {v[k]:.3f}°C (trial {x[k]})')
    ax.set_xlabel('Trial'); ax.set_ylabel('Validation MAE (°C)')
    ax.set_title('(a) XGBoost, Spatial-ClimStrat, Continental zone', fontsize=13, loc='left')
    ax.set_xticks(np.arange(0, len(x) + 1, 5)); ax.set_xlim(0.5, len(x) + 0.5)
    ax.grid(alpha=0.3); ax.legend(fontsize=10, framealpha=0.9)
    caption['Continental'] = {'best_MAE': round(float(v[k]), 4), 'best_trial': int(x[k]),
                              'first_trial_MAE': round(float(v[0]), 4),
                              'range': [round(float(v.min()), 4), round(float(v.max()), 4)],
                              'last5_spread': round(float(b[-5:].max() - b[-5:].min()), 4)}

    # (b) the three climate zones
    ax = axes[1]
    for zone, label in ZONES:
        x, v, b = history(zone)
        ax.plot(x, b, '-', color=COLORS[label], lw=2.2, label=f'{label}: {b[-1]:.3f}°C')
        ax.plot(x, v, 'o', color=COLORS[label], ms=3.5, alpha=0.35)
        caption[label] = {'best_MAE': round(float(b[-1]), 4), 'best_trial': int(np.argmin(v) + 1),
                          'first_trial_MAE': round(float(v[0]), 4),
                          'range': [round(float(v.min()), 4), round(float(v.max()), 4)],
                          'last5_spread': round(float(b[-5:].max() - b[-5:].min()), 4)}
    ax.set_xlabel('Trial'); ax.set_ylabel('Validation MAE (°C)')
    ax.set_title('(b) Best-so-far across climate zones (dots: individual trials)', fontsize=13, loc='left')
    ax.set_xticks(np.arange(0, len(x) + 1, 5)); ax.set_xlim(0.5, len(x) + 0.5)
    ax.grid(alpha=0.3); ax.legend(fontsize=10, framealpha=0.9)

    fig.tight_layout()
    for ext in ['png', 'pdf']:
        fig.savefig(os.path.join(FIG, f'figureS1_convergence_real.{ext}'), dpi=300,
                    bbox_inches='tight', facecolor='white')

    # numbers the new caption must quote, plus how far the best trial sits from trial 1
    caption['_note'] = (f'Real Optuna TPE histories (seed 42, {len(x)} trials) recorded by rerun_models.py; '
                        'validation MAE is unweighted, on the 16 % validation subset of the training rows.')
    json.dump(caption, open(os.path.join(FIG, 'figureS1_caption_numbers.json'), 'w'), indent=1)
    print(json.dumps(caption, indent=1))


if __name__ == '__main__':
    main()
