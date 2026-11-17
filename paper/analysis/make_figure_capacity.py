"""SI figure: how the value of stratification changes with the number of boosting rounds.

Panel (a) is the validation MAE of the national model and of the two stratified designs (each
pooled over its three strata, weighted by validation rows) after every boosting round; panel (b) is
the difference of each stratified design from the national model, in percent. A dotted line marks
the ceiling of 1,000 rounds in the original search. Data: capacity_curves.py.

Output: figures/figureS_capacity_curves.{png,pdf} and <PA_OUT>/figures/capacity_caption_numbers.json
Usage : PA_OUT=paper/results_wide python3 paper/analysis/make_figure_capacity.py
        (PA_CURVES=<file> draws from another curves file)
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, '..', 'results_wide')
SRC = os.environ.get('PA_CURVES') or os.path.join(BASE, 'capacity_curves.json')
OLD_CEILING = 1000

plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['font.size'] = 10
C = {'nat': '#2E86AB', 'ts': '#E07A1F', 'cs': '#52A06E'}

r = json.load(open(SRC))
nat = np.array(r['National']['curve'])


def pooled(prefix):
    ks = [k for k in r if k.startswith(prefix + ':')]
    assert len(ks) == 3, (prefix, ks)
    n = sum(r[k]['n_val'] for k in ks)
    assert n == r['National']['n_val'], 'strata must partition the validation rows'
    return sum(np.array(r[k]['curve']) * r[k]['n_val'] for k in ks) / n


ts, cs = pooled('TempStrat'), pooled('ClimStrat')
N = len(nat)
x = np.arange(1, N + 1)
d_ts, d_cs = 100 * (ts / nat - 1), 100 * (cs / nat - 1)


def crossing(d):
    """First round after which the stratified design is no longer more accurate (d >= 0), or None."""
    neg = np.where(d < 0)[0]
    if len(neg) == 0:
        return None
    after = np.where(d[neg[0]:] >= 0)[0]
    return int(neg[0] + after[0] + 1) if len(after) else None


fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.2))
a.plot(x, nat, color=C['nat'], lw=2.6, label='National (one model)')
a.plot(x, ts, color=C['ts'], lw=2, ls='--', label='Temperature-stratified (3 models, pooled)')
a.plot(x, cs, color=C['cs'], lw=2, ls='-.', label='Climate-zone-stratified (3 models, pooled)')
lo, hi = min(nat.min(), ts.min(), cs.min()), max(nat[49], ts[49], cs[49])
a.set_ylim(lo - 0.02, hi + 0.02)
a.annotate(f'{nat[OLD_CEILING - 1]:.3f}', (OLD_CEILING, nat[OLD_CEILING - 1]), xytext=(6, 6),
           textcoords='offset points', fontsize=8.5, color=C['nat'], fontweight='bold')
a.annotate(f'{nat[-1]:.3f}', (N, nat[-1]), xytext=(-4, 7), textcoords='offset points',
           ha='right', fontsize=8.5, color=C['nat'], fontweight='bold')
a.set_ylabel('Validation MAE (°C)', fontsize=12, fontweight='bold')
a.set_title('(a) Validation error', fontsize=12, fontweight='bold', loc='left')

b.axhline(0, color='black', lw=1)
b.plot(x, d_ts, color=C['ts'], lw=2, ls='--', label='Temperature-stratified')
b.plot(x, d_cs, color=C['cs'], lw=2, ls='-.', label='Climate-zone-stratified')
span = max(abs(d_ts[49:]).max(), abs(d_cs[49:]).max())
ylo, yhi = -span * 1.15, max(abs(d_ts[-1]), abs(d_cs[-1]), 2) * 1.3
b.set_ylim(ylo, yhi)
b.fill_between([50, N], 0, yhi, color=C['nat'], alpha=0.06)
b.fill_between([50, N], ylo, 0, color='#999999', alpha=0.06)
b.text(60, yhi * 0.88, 'National more accurate', fontsize=9.5, color=C['nat'], fontweight='bold', va='center')
b.text(60, ylo * 0.92, 'Stratified more accurate', fontsize=9.5, color='#555555', fontweight='bold', va='center')
for d, key in [(d_ts, 'ts'), (d_cs, 'cs')]:
    c = crossing(d)
    if c:
        b.annotate(f'crosses at {c:,} rounds', (c, 0), xytext=(c * 2.2, ylo * 0.45), fontsize=9, color=C[key],
                   arrowprops=dict(arrowstyle='->', color=C[key]))
    v = d[-1]
    b.annotate(f'{v:+.1f}%', (N, v), xytext=(-6, 6 if v > 0 else -13), textcoords='offset points',
               ha='right', fontsize=9, fontweight='bold', color=C[key])
b.set_ylabel('Stratified vs national MAE (%)', fontsize=12, fontweight='bold')
b.set_title('(b) Difference from the national model', fontsize=12, fontweight='bold', loc='left')

for ax in (a, b):
    ax.axvline(OLD_CEILING, color='gray', lw=1.2, ls=':')
    # panel (a): left of the line at mid-height, where the curves have already fallen away;
    # panel (b): right of the line at the top
    y0, y1 = ax.get_ylim()
    if ax is a:
        ax.text(OLD_CEILING * 0.94, y0 + 0.55 * (y1 - y0), 'original search\nceiling (1,000)',
                fontsize=8.5, color='gray', ha='right', va='center')
    else:
        ax.text(OLD_CEILING * 1.06, y1 - 0.02 * (y1 - y0), 'original search\nceiling (1,000)',
                fontsize=8.5, color='gray', va='top')
    ax.set_xscale('log'); ax.set_xlim(50, N)
    ax.set_xlabel('Number of boosting rounds (trees)', fontsize=12, fontweight='bold')
    ax.grid(True, which='both', alpha=0.3, ls='--')
a.legend(fontsize=9.5, framealpha=0.95, edgecolor='gray', loc='upper right')
b.legend(fontsize=9.5, loc='lower right', framealpha=0.95, edgecolor='gray')
plt.tight_layout()
FIGDIR = os.environ.get('PA_FIG_DIR') or os.path.join(ROOT, 'figures')   # PA_FIG_DIR: draw elsewhere first
os.makedirs(FIGDIR, exist_ok=True)
for ext in ('png', 'pdf'):
    plt.savefig(os.path.join(FIGDIR, f'figureS_capacity_curves.{ext}'), dpi=300,
                bbox_inches='tight', facecolor='white')

nums = {'source': os.path.relpath(SRC, ROOT), 'rounds': N,
        'national_at_1000': float(nat[OLD_CEILING - 1]), 'national_at_end': float(nat[-1]),
        'tempstrat_pct_at_1000': float(d_ts[OLD_CEILING - 1]), 'tempstrat_pct_at_end': float(d_ts[-1]),
        'climstrat_pct_at_1000': float(d_cs[OLD_CEILING - 1]), 'climstrat_pct_at_end': float(d_cs[-1]),
        'tempstrat_crossing_round': crossing(d_ts), 'climstrat_crossing_round': crossing(d_cs)}
os.makedirs(os.path.join(BASE, 'figures'), exist_ok=True)
json.dump(nums, open(os.path.join(BASE, 'figures', 'capacity_caption_numbers.json'), 'w'), indent=1)
print(json.dumps(nums, indent=1))
