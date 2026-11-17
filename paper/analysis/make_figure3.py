"""Figure 3: monthly and hourly MAE, uncalibrated vs calibrated, from the re-run national model.

Redraws the published Figure 3 in the same style (two panels, each with a broken y-axis so the
~6 C uncalibrated error and the ~0.7 C calibrated error are both readable) but from the numbers
produced by the unified re-run rather than the original pipeline. The published figure was drawn
from a different model run than the one the text quoted: its calibrated curve spans 0.59-0.68
while Section 4.2 quoted 0.70-0.79. Both now come from the same source.

Input : <PA_OUT>/error_by_month.csv and error_by_hour.csv, written by error_timing.py.
Output: <PA_OUT>/figures/figure3.{png,pdf}
Usage : PA_OUT=analysis_R1/results50 python3 analysis_R1/make_figure3.py
"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
FIG = os.path.join(BASE, 'figures'); os.makedirs(FIG, exist_ok=True)

RAW_C, CAL_C = '#7E8C8D', '#2F4454'          # grey = uncalibrated, dark slate = calibrated
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

plt.rcParams.update({'font.family': 'Arial', 'font.size': 17, 'axes.unicode_minus': False,
                     'axes.linewidth': 1.6, 'xtick.major.width': 1.6, 'ytick.major.width': 1.6})


def pad(lo, hi, f=0.12):
    m = (hi - lo) * f or 0.05
    return lo - m, hi + m


def panel(ax_hi, ax_lo, x, raw, cal, xticks, xticklabels, xlabel, letter, legend=False):
    for ax in (ax_hi, ax_lo):
        ax.plot(x, raw, '-o', color=RAW_C, lw=2.2, ms=8, mfc=RAW_C, mec=RAW_C,
                label='Uncalibrated sensor error', clip_on=True)
        ax.plot(x, cal, '-^', color=CAL_C, lw=2.2, ms=9, mfc='white', mec=CAL_C, mew=2.0,
                label='Calibrated sensor error', clip_on=True)
        ax.set_xticks(xticks)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)

    ax_hi.set_ylim(*pad(raw.min(), raw.max()))
    ax_lo.set_ylim(*pad(cal.min(), cal.max()))
    # at most two decimals on the calibrated axis: three-decimal labels run into the shared y label
    ax_lo.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
    ax_hi.spines['bottom'].set_visible(False)
    ax_hi.tick_params(bottom=False, labelbottom=False)
    ax_lo.set_xticklabels(xticklabels)
    ax_lo.set_xlabel(xlabel, fontweight='bold', labelpad=10)

    # the diagonal break marks, drawn in axes coordinates on both halves
    kw = dict(marker=[(-1, -0.6), (1, 0.6)], markersize=13, linestyle='none',
              color='k', mec='k', mew=1.6, clip_on=False)
    ax_hi.plot([0], [0], transform=ax_hi.transAxes, **kw)
    ax_lo.plot([0], [1], transform=ax_lo.transAxes, **kw)

    ax_hi.text(0.02, 0.93, letter, transform=ax_hi.transAxes, fontsize=21,
               fontweight='bold', va='top', ha='left')
    if legend:
        ax_lo.legend(loc='lower left', frameon=False, fontsize=16, handlelength=2.4,
                     borderaxespad=0.6)


def main():
    m = pd.read_csv(os.path.join(BASE, 'error_by_month.csv')).sort_values('month')
    h = pd.read_csv(os.path.join(BASE, 'error_by_hour.csv')).sort_values('hour')

    # the published figure3.png is 3192x1754 at 300 dpi; matching that geometry keeps the panel
    # proportions and the relative text size of the submitted version, which has no source script
    fig = plt.figure(figsize=(3192 / 300, 1754 / 300))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.07, wspace=0.18)
    axes = [[fig.add_subplot(gs[r, c]) for r in (0, 1)] for c in (0, 1)]

    panel(axes[0][0], axes[0][1], m['month'].values, m['raw_MAE'].values, m['cal_MAE'].values,
          xticks=[1, 3, 5, 7, 9, 11], xticklabels=[MONTHS[i - 1] for i in [1, 3, 5, 7, 9, 11]],
          xlabel='Month', letter='(a)', legend=True)
    for lab in axes[0][1].get_xticklabels():
        lab.set_rotation(45); lab.set_ha('right')

    panel(axes[1][0], axes[1][1], h['hour'].values, h['raw_MAE'].values, h['cal_MAE'].values,
          xticks=[0, 4, 8, 12, 16, 20], xticklabels=['0', '4', '8', '12', '16', '20'],
          xlabel='Hour of Day', letter='(b)')

    fig.supylabel('MAE (°C)', fontweight='bold', fontsize=13, x=0.035)
    fig.subplots_adjust(left=0.105, right=0.985, top=0.96, bottom=0.17)

    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(FIG, f'figure3.{ext}'), dpi=300, facecolor='white')
    print(f"figure3 written to {FIG}")
    print(f"  monthly  raw {m.raw_MAE.min():.2f}-{m.raw_MAE.max():.2f}  "
          f"cal {m.cal_MAE.min():.3f}-{m.cal_MAE.max():.3f} (peak {MONTHS[int(m.cal_MAE.idxmax())]})")
    print(f"  hourly   raw {h.raw_MAE.min():.2f}-{h.raw_MAE.max():.2f} (peak {int(h.loc[h.raw_MAE.idxmax(),'hour'])}:00)  "
          f"cal {h.cal_MAE.min():.3f}-{h.cal_MAE.max():.3f} (peak {int(h.loc[h.cal_MAE.idxmax(),'hour'])}:00)")


if __name__ == '__main__':
    main()
