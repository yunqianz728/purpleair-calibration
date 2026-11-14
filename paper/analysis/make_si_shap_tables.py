"""SI Tables S6 and S7: top-25 features by SHAP importance, pooled over the three temperature strata.

Reads the per-stratum SHAP summaries that make_figure5.py writes (figure5_groups.json for the
temperature-error target, figure_s2_groups.json for station temperature) and pools them with equal
weight, which is what an equal number of test rows per stratum amounts to. Prints the LaTeX body
rows for each table so they can be pasted into si.tex.

Usage: PA_OUT=analysis_R1/results50 python3 analysis_R1/make_si_shap_tables.py
"""
import json, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.environ.get('PA_OUT') or os.path.join(HERE, 'results'), 'figures')
STRATA = ['Cold', 'Normal', 'Hot']
TOPN = 25

SHORT = {'elevation_sensor': 'elev', 'sensor_lat': 'lat', 'sensor_lon': 'lon', 'sensor_tcc': 'TCC',
         'temp_ma_3h': 'temp_avg_3h', 'temp_ma_6h': 'temp_avg_6h', 'temp_ma_12h': 'temp_avg_12h',
         'temp_std_3h': 'temp_sd_3h', 'temp_std_6h': 'temp_sd_6h', 'temp_std_12h': 'temp_sd_12h',
         'hour_cos': 'cos(hour)', 'hour_sin': 'sin(hour)', 'month_cos': 'cos(month)',
         'month_sin': 'sin(month)', 'dewpoint_depression_sensor': 'dewpoint_dep',
         'dewpoint_sensor': 'dewpoint', 'vapor_pressure_deficit_sensor': 'VPD',
         'humidity_squared': 'RH$^2$', 'humidity': 'RH', 'sensor temperature': 'temp',
         'temp_squared_sensor': 'temp$^2$', 'temp_humidity_product_sensor': 'temp $\\times$ RH',
         'temp_life_interaction_sensor': 'temp $\\times$ age', 'diurnal_radiation': 'diurnal_rad',
         'ssrd': 'SSRD', 'strd': 'STRD', 'sshf': 'SSHF', 'ssrd_1h_ago': 'SSRD_1h',
         'ssrd_2h_ago': 'SSRD_2h', 'ssrd_change': 'SSRD_chg', 'ssrd_sum_3h': 'SSRD_sum_3h',
         'ssrd_sum_6h': 'SSRD_sum_6h',
         'polar_day_night': 'polar_day', 'tp': 'precipitation',
         'temp_acceleration': 'temp_accel'}
SHORT.update({f'humidity_{h}h_ago': f'humidity_{h}h' for h in range(1, 4)})
SHORT.update({f'sensor_temp_{h}h_ago': f'temp_{h}h' for h in range(1, 7)})


def tex(name):
    return SHORT.get(name, name).replace('_', '\\_')


def table(path, label):
    d = json.load(open(os.path.join(FIG, path)))
    a = pd.DataFrame({s: d[s]['feature_mean_abs'] for s in STRATA}).mean(axis=1)
    g = pd.DataFrame({s: d[s]['feature_mean_signed'] for s in STRATA}).mean(axis=1)
    pct = 100 * a / a.sum()
    top = a.sort_values(ascending=False).head(TOPN)
    print(f'% ---- {label} (pooled over {", ".join(STRATA)}; '
          f'{d["Cold"]["n_rows_pie"]} rows per stratum)')
    for i, f in enumerate(top.index, start=1):
        sign = '+' if g[f] >= 0 else '-'
        print(f'{i} & {tex(f)} & {a[f]:.3f} & {pct[f]:.2f} & $' + sign + f'{abs(g[f]):.3f}$ \\\\')
    print(f'% top-25 covers {pct[top.index].sum():.1f}% of total importance\n')


if __name__ == '__main__':
    table('figure5_groups.json', 'Table S6: target temperature error')
    table('figure_s2_groups.json', 'Table S7: target station temperature')
