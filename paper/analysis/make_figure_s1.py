"""SI Figure S1, drawn with the plotting code of the submitted figure and the recorded Optuna histories.

The submitted Figure S1 came from notebooks/PA_final_modified.ipynb (cell 5). Its plotting code is
kept here as it was: the figure size, colours, the Continental curve with white-edged markers, the
faint dashed Arid and Temperate reference curves, the red star and dashed line at the best value,
the boxed values at key trials, the titles, axis labels, grid and legend. Two things change, both
because the old figure stated what the data do not:

  * the data. The old curves came from `generate_realistic_convergence()`, which builds a smooth
    descent towards a target MAE with added noise. Here each curve is the best validation MAE reached
    so far in the actual 50-trial Optuna search recorded by rerun_models.py for the same
    configuration (XGBoost, Spatial-ClimStrat, temperature-error target).
  * the three shaded phases and their labels ("Rapid Descent / Stabilization / Fine-tuning",
    trials 1-10 / 11-15 / 16-20) are not drawn. They were properties of the generator, fixed in
    advance, and the recorded histories do not divide that way.

The key trials annotated, the x-axis ticks and limits follow the same rule as before, stretched from
20 trials to the 50 that were run.

Output: figures/figureS1_convergence_real.{png,pdf} and <PA_OUT>/figures/figureS1_caption_numbers.json
Usage : PA_OUT=analysis_R1/results50 python3 analysis_R1/make_figure_s1.py
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
M = os.path.join(BASE, 'models')
CONFIG = 'Spatial-ClimStrat__temp_error__'

# ---- style, as in the original cell
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10


def history(zone):
    """Trial numbers, each trial's validation MAE, and the best reached so far."""
    t = sorted(json.load(open(os.path.join(M, CONFIG + zone + '.json')))['trials'], key=lambda x: x['trial'])
    v = np.array([x['val_MAE'] for x in t])
    return np.arange(1, len(v) + 1), v, np.minimum.accumulate(v)


trials, raw_continental, mae_continental = history('D_Continental')
_, raw_arid, mae_arid = history('B_Arid')
_, raw_temperate, mae_temperate = history('C_Temperate')
n_trials = len(trials)

fig, ax = plt.subplots(figsize=(12, 7))

# reference lines (other climate zones), faint and dashed
ax.plot(trials, mae_arid, '--', linewidth=1.5, alpha=0.3,
        color='#E85D75', label='Arid zone (reference)', zorder=1)
ax.plot(trials, mae_temperate, '--', linewidth=1.5, alpha=0.3,
        color='#52B788', label='Temperate zone (reference)', zorder=1)

# main curve: Continental (Cold), highlighted
ax.plot(trials, mae_continental, 'o-', linewidth=2.8, markersize=8,
        color='#2E86AB', markerfacecolor='#3A5BA0',
        markeredgewidth=1.5, markeredgecolor='white',
        label='Continental (Cold) - Primary Model', zorder=3)

# best point
best_trial = int(np.argmin(mae_continental)) + 1
best_mae = mae_continental[best_trial - 1]
ax.scatter([best_trial], [best_mae], s=400, c='red', marker='*',
           edgecolors='darkred', linewidths=2.5, zorder=5,
           label=f'Best MAE: {best_mae:.4f}°C (Trial {best_trial})')
ax.axhline(y=best_mae, color='red', linestyle='--', linewidth=1.5, alpha=0.5, zorder=2)

# values at key trials: first, last, and evenly between (1, 5, 10, 15, 20 for the old 20 trials)
key_trials = [1] + list(range(10, n_trials + 1, 10))
for trial_idx in key_trials:
    mae_val = mae_continental[trial_idx - 1]
    ax.annotate(f'{mae_val:.3f}',
                xy=(trial_idx, mae_val),
                xytext=(0, 12 if trial_idx <= 10 else -15),
                textcoords='offset points',
                ha='center', fontsize=9, fontweight='bold',
                color='#2E86AB',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor='#2E86AB', alpha=0.9, linewidth=1))

ax.set_xlabel('Trial Number', fontsize=13, fontweight='bold')
ax.set_ylabel('Validation MAE (°C)', fontsize=13, fontweight='bold')
ax.set_title('Convergence Behavior of Bayesian Optimization for XGBoost\n' +
             '(Temperature Error Prediction - Continental Climate Zone)',
             fontsize=14, fontweight='bold', pad=20)

ax.set_xlim(0, n_trials + 1)
top = max(mae_continental.max(), mae_arid.max(), mae_temperate.max())
bottom = min(mae_continental.min(), mae_arid.min(), mae_temperate.min())
ax.set_ylim(bottom * 0.95, top * 1.03)
ax.set_xticks(range(0, n_trials + 2, 5))

ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8, zorder=0)

handles, labels = ax.get_legend_handles_labels()
order = [2, 3, 0, 1]   # main curve and best value first, as before
ax.legend([handles[i] for i in order], [labels[i] for i in order],
          loc='upper right', fontsize=10, framealpha=0.95,
          edgecolor='gray', fancybox=True)

plt.tight_layout()
for ext in ('png', 'pdf'):
    plt.savefig(os.path.join(ROOT, 'figures', f'figureS1_convergence_real.{ext}'),
                dpi=300, bbox_inches='tight', facecolor='white')
plt.close('all')

# numbers the caption quotes
out = {}
for name, raw, best in [('Continental', raw_continental, mae_continental),
                        ('Arid', raw_arid, mae_arid), ('Temperate', raw_temperate, mae_temperate)]:
    out[name] = {'best_MAE': round(float(best[-1]), 4), 'best_trial': int(np.argmin(raw)) + 1,
                 'first_trial_MAE': round(float(raw[0]), 4),
                 'last5_spread': round(float(best[-5:].max() - best[-5:].min()), 4)}
out['_note'] = ('Best-so-far validation MAE of the recorded Optuna TPE search (seed 42, 50 trials), XGBoost '
                'Spatial-ClimStrat, temperature-error target; validation MAE is unweighted, on the 16 % '
                'validation subset of the training rows.')
os.makedirs(os.path.join(BASE, 'figures'), exist_ok=True)
json.dump(out, open(os.path.join(BASE, 'figures', 'figureS1_caption_numbers.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
