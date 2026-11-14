"""
Feature Importance Analysis - temp_error target version
Generates Figure 5 using Temporal-TempStrat temp_error XGBoost models.
All plotting parameters identical to figure5_improved.py.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import pickle
import shap
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 30
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['text.usetex'] = False
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['mathtext.default'] = 'regular'

# =====================================================================
# Configuration
# =====================================================================
# NEW: temp_error models
# R1 revision: all plotting code below is unchanged. Only the models and the rows they are
# explained on have moved -- to the re-run models in analysis_R1/results50 and to that run's
# held-out test rows, so the figure matches Table 2 and SI Table S8.
import os, json
BASE = os.environ.get('PA_OUT', 'analysis_R1/results50')
MODEL_PATHS = {k: f'{BASE}/models/Temporal-TempStrat__temp_error__{k}.ubj' for k in ['Cold', 'Normal', 'Hot']}

DATA_PATH = os.environ['PA_PARQUET']
OUTPUT_FIGURE = os.environ.get('PA_FIG5_OUT', 'figures/figure5.png')

SHAP_SAMPLE_SIZE = 2000
MAX_DISPLAY = 10

# Also generate station_temp version for SI
MODEL_PATHS_STATION = {k: f'{BASE}/models/Temporal-TempStrat__station_temp__{k}.ubj' for k in ['Cold', 'Normal', 'Hot']}
OUTPUT_FIGURE_SI = os.environ.get('PA_FIGS2_OUT', 'figures/figure_s2_shap_station_temp.png')

FEATURE_ACRONYMS = {
    'sensor temperature': 'temp', 'humidity': 'humidity',
    'sensor_lat': 'lat', 'sensor_lon': 'lon', 'elevation_sensor': 'elev',
    'sensor_tcc': 'TCC', 'life': 'life',
    'ssrd': 'SSRD', 'strd': 'STRD', 'sshf': 'SSHF',
    'diurnal_radiation': 'diurnal_rad',
    'tp': 'precipitation', 'u10': 'u10', 'v10': 'v10',
    'wind_speed': 'wind_speed', 'wind_direction': 'wind_dir',
    'year': 'year', 'month': 'month', 'day': 'day', 'hour': 'hour',
    'day_of_month': 'day_of_month',
    'hour_sin': 'sin(hour)', 'hour_cos': 'cos(hour)',
    'month_sin': 'sin(month)', 'month_cos': 'cos(month)',
    'dewpoint_sensor': 'dewpoint', 'dewpoint_depression_sensor': 'dewpoint_dep',
    'vapor_pressure_deficit_sensor': 'VPD',
    'humidity_squared': r'humidity²', 'temp_squared_sensor': r'temp²',
    'temp_humidity_product_sensor': r'temp$\times$humidity',
    'temp_life_interaction_sensor': r'temp$\times$life',
    'sensor_temp_1h_ago': 'temp_1h', 'sensor_temp_2h_ago': 'temp_2h',
    'sensor_temp_3h_ago': 'temp_3h', 'sensor_temp_4h_ago': 'temp_4h',
    'sensor_temp_5h_ago': 'temp_5h', 'sensor_temp_6h_ago': 'temp_6h',
    'humidity_1h_ago': 'humidity_1h', 'humidity_2h_ago': 'humidity_2h',
    'humidity_3h_ago': 'humidity_3h',
    'ssrd_1h_ago': 'SSRD_1h', 'ssrd_2h_ago': 'SSRD_2h',
    'temp_ma_3h': 'temp_avg_3h', 'temp_ma_6h': 'temp_avg_6h',
    'temp_ma_12h': 'temp_avg_12h',
    'temp_std_3h': 'temp_sd_3h', 'temp_std_6h': 'temp_sd_6h',
    'temp_std_12h': 'temp_sd_12h',
    'temp_range_3h': 'temp_range_3h', 'temp_range_6h': 'temp_range_6h',
    'temp_change_1h': 'temp_change_1h', 'temp_change_2h': 'temp_change_2h',
    'temp_change_3h': 'temp_change_3h',
    'temp_trend_3h': 'temp_trend_3h', 'temp_trend_6h': 'temp_trend_6h',
    'temp_acceleration': 'temp_accel', 'ssrd_change': 'SSRD_change',
    'ssrd_sum_3h': 'SSRD_sum_3h', 'ssrd_sum_6h': 'SSRD_sum_6h',
    'hot_streak': 'hot_streak', 'cold_streak': 'cold_streak',
    'polar_day_night': 'polar_day_night', 'is_hot': 'is_hot', 'is_cold': 'is_cold',
}

FEATURE_GROUPS = {
    'Temporal': [
        'sensor_temp_1h_ago', 'sensor_temp_2h_ago', 'sensor_temp_3h_ago',
        'sensor_temp_4h_ago', 'sensor_temp_5h_ago', 'sensor_temp_6h_ago',
        'temp_ma_3h', 'temp_ma_6h', 'temp_ma_12h',
        'temp_std_3h', 'temp_std_6h', 'temp_std_12h',
        'temp_change_1h', 'temp_change_2h', 'temp_change_3h',
        'temp_trend_3h', 'temp_trend_6h', 'temp_acceleration',
        'temp_range_3h', 'temp_range_6h',
        'hot_streak', 'cold_streak',
        'humidity_1h_ago', 'humidity_2h_ago', 'humidity_3h_ago',
        'ssrd_1h_ago', 'ssrd_2h_ago',
        'ssrd_sum_3h', 'ssrd_sum_6h', 'ssrd_change'
    ],
    'Temperature': [
        'sensor temperature', 'temp_squared_sensor',
        'temp_humidity_product_sensor', 'temp_life_interaction_sensor'
    ],
    'Radiation': ['ssrd', 'strd', 'sshf', 'diurnal_radiation'],
    'Humidity': [
        'humidity', 'humidity_squared', 'dewpoint_sensor',
        'dewpoint_depression_sensor', 'vapor_pressure_deficit_sensor',
        'humidity_original', 'dewpoint_original'
    ],
    'Geographic': [
        'sensor_lat', 'sensor_lon', 'elevation_sensor', 'sensor_tcc',
        'station_lat', 'station_lon', 'elevation_station', 'station_tcc',
        'distance', 'delta_elev', 'delta_tcc'
    ],
    'Other': [
        'day', 'month', 'hour', 'year', 'life', 'day_of_month',
        'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
        'tp', 'polar_day_night', 'is_hot', 'is_cold',
        'utc_offset', 'matched_lon', 'matched_lat', 'lon_diff', 'lat_diff',
        'u10', 'v10', 'wind_speed', 'wind_direction'
    ]
}

GROUP_COLORS = {
    'Temporal': '#E74C3C', 'Temperature': '#F39C12', 'Radiation': '#9B59B6',
    'Humidity': '#3498DB', 'Geographic': '#2ECC71', 'Other': '#95A5A6'
}

# =====================================================================
# Helper functions (identical to figure5_improved.py)
# =====================================================================
def load_model(model_path):
    if model_path.endswith('.ubj'):          # the re-run saves boosters, not pickles
        import xgboost as xgb
        m = xgb.XGBRegressor()
        m.load_model(model_path)
        return m
    with open(model_path, 'rb') as f:
        model_dict = pickle.load(f)
    if isinstance(model_dict, dict):
        if 'model' in model_dict:
            return model_dict['model']
        elif 'estimator' in model_dict:
            return model_dict['estimator']
        else:
            for key, value in model_dict.items():
                if hasattr(value, 'predict'):
                    return value
    return model_dict


def calculate_group_importance(shap_values, feature_names):
    feature_importance = np.abs(shap_values).mean(axis=0)
    importance_df = pd.DataFrame({'feature': feature_names, 'importance': feature_importance})
    group_importance = {}
    for group_name, group_features in FEATURE_GROUPS.items():
        group_total = importance_df[importance_df['feature'].isin(group_features)]['importance'].sum()
        group_importance[group_name] = group_total
    total = sum(group_importance.values())
    if total > 0:
        group_importance = {k: v/total*100 for k, v in group_importance.items()}
    return group_importance


def add_pie_with_labels(ax_pie, group_importance, show_legend=False):
    min_percentage = 1.0
    filtered_groups = {k: v for k, v in group_importance.items() if v > min_percentage}
    other_sum = sum([v for k, v in group_importance.items() if v <= min_percentage])
    if other_sum > 0:
        filtered_groups['Others'] = other_sum
    sorted_groups = sorted(filtered_groups.items(), key=lambda x: x[1], reverse=True)
    groups = [g for g, _ in sorted_groups]
    values = [v for _, v in sorted_groups]
    colors = [GROUP_COLORS.get(g, '#95A5A6') for g in groups]

    wedges, texts = ax_pie.pie(values, labels=None, colors=colors, startangle=45,
                                wedgeprops={'edgecolor': 'white', 'linewidth': 2})

    small_labels_info = []
    for i, (wedge, value, group) in enumerate(zip(wedges, values, groups)):
        if value < 8:
            ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
            small_labels_info.append({'idx': i, 'ang': ang, 'value': value})

    for i, (wedge, value, group) in enumerate(zip(wedges, values, groups)):
        ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        if value < 8:
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            x_offset = 1.4 * np.sign(x)
            y_offset = 1.4 * y
            same_side_small = [info for info in small_labels_info
                               if np.sign(np.cos(np.deg2rad(info['ang']))) == np.sign(x)]
            if len(same_side_small) > 1:
                current_idx_in_side = next(
                    (idx for idx, info in enumerate(same_side_small) if info['idx'] == i), 0)
                y_offset = y_offset + current_idx_in_side * 0.2
            ax_pie.annotate(f'{value:.0f}%', xy=(x, y), xycoords='data',
                           xytext=(x_offset, y_offset), textcoords='data',
                           ha=horizontalalignment, size=23,
                           arrowprops=dict(arrowstyle="-", lw=1.0,
                                          connectionstyle=connectionstyle, color='gray'))
        else:
            ax_pie.text(0.7*x, 0.7*y, f'{value:.0f}%', ha='center', va='center',
                       fontsize=25, color='white', fontweight='bold')
    ax_pie.set_aspect('equal')
    return wedges, groups


def generate_figure(model_paths, output_path, xlabel_suffix=""):
    """Generate a SHAP figure from given model paths."""
    print(f"\nGenerating: {output_path}")

    df = pd.read_parquet(DATA_PATH)
    # explain the model on its own held-out rows, the same 20% split the re-run scored on
    from sklearn.model_selection import train_test_split
    _, te = train_test_split(df.index.values, test_size=0.2, random_state=42)
    df = df.loc[te]
    fig = plt.figure(figsize=(14, 18))
    gs = fig.add_gridspec(3, 1, hspace=0.35, wspace=0.1,
                          left=0.08, right=0.95, top=0.94, bottom=0.06)

    shap_data = {}
    x_mins, x_maxs = [], []
    all_axes = []
    all_wedges = []
    all_groups = []

    # Pass 1: compute SHAP
    for idx, (stratum, model_path) in enumerate(model_paths.items()):
        print(f"  Computing SHAP for {stratum}...")
        model = load_model(model_path)
        stratum_data = df[df['Temperature class'] == stratum]

        if hasattr(model, 'feature_names_in_'):
            feature_cols = list(model.feature_names_in_)
        else:
            feature_cols = list(model.get_booster().feature_names)

        sample_size = min(SHAP_SAMPLE_SIZE, len(stratum_data))
        sample_data = stratum_data.sample(n=sample_size, random_state=42)
        X_sample = sample_data.copy()
        for feature in feature_cols:
            if feature not in X_sample.columns:
                X_sample[feature] = 0
        X_sample = X_sample[feature_cols].fillna(X_sample[feature_cols].mean())

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        group_importance = calculate_group_importance(shap_values, feature_cols)

        shap_data[stratum] = {
            'shap_values': shap_values, 'X_sample': X_sample,
            'group_importance': group_importance, 'idx': idx
        }
        x_mins.append(shap_values.min())
        x_maxs.append(shap_values.max())

    # Unified x-axis
    x_range = max(abs(min(x_mins)), abs(max(x_maxs)))
    xlim = (-x_range * 1.05, x_range * 1.05)

    # Pass 2: plot
    for stratum in ['Cold', 'Normal', 'Hot']:
        data = shap_data[stratum]
        idx = data['idx']

        ax = plt.subplot(gs[idx, 0])
        all_axes.append(ax)

        X_renamed = data['X_sample'].copy()
        X_renamed.columns = [FEATURE_ACRONYMS.get(c, c) for c in X_renamed.columns]

        shap.summary_plot(data['shap_values'], X_renamed, max_display=MAX_DISPLAY,
                         show=False, plot_size=None, color_bar=False)

        current_ax = plt.gca()
        current_ax.set_xlim(xlim)

        labels = ['(a)', '(b)', '(c)']
        titles = ['Cold Temperature Stratum', 'Moderate Temperature Stratum',
                  'Hot Temperature Stratum']
        current_ax.text(-0.08, 1.03, f'{labels[idx]} {titles[idx]}',
                       transform=current_ax.transAxes,
                       fontsize=25, fontweight='bold', va='top', ha='left')

        if idx == 2:
            lbl = 'SHAP value (impact on model output)'
            if xlabel_suffix:
                lbl = f'SHAP value (impact on predicted {xlabel_suffix})'
            current_ax.set_xlabel(lbl, fontsize=23)
        else:
            current_ax.set_xlabel('')

        current_ax.axvline(x=0, color='black', linestyle='-', linewidth=1.2, alpha=0.5)
        current_ax.spines['top'].set_visible(False)
        current_ax.spines['right'].set_visible(False)
        current_ax.tick_params(axis='y', labelsize=22)
        current_ax.tick_params(axis='x', labelsize=22)
        for label in current_ax.get_yticklabels():
            label.set_horizontalalignment('left')
            label.set_x(-0.02)

        # Pie chart
        bbox = current_ax.get_position()
        pie_x = bbox.x0 + bbox.width * 0.32
        pie_y = bbox.y0 + bbox.height * 0.0
        pie_width = bbox.width * 1.0
        pie_height = bbox.height * 0.85
        ax_pie = fig.add_axes([pie_x, pie_y, pie_width, pie_height])
        wedges, groups = add_pie_with_labels(ax_pie, data['group_importance'])
        all_wedges.append(wedges)
        all_groups.append(groups)

    # Legend
    unique_groups = []
    seen = set()
    for gl in all_groups:
        for g in gl:
            if g not in seen and g != 'Others':
                unique_groups.append(g)
                seen.add(g)
    legend_elements = [mpatches.Patch(color=GROUP_COLORS[g], label=g) for g in unique_groups
                       if g in GROUP_COLORS]
    if any('Others' in gl for gl in all_groups):
        legend_elements.append(mpatches.Patch(color='#95A5A6', label='Others'))

    if all_axes:
        bbox = all_axes[0].get_position()
        fig.legend(handles=legend_elements, loc='lower left',
                  bbox_to_anchor=(bbox.x0 + 0.12, bbox.y0 + 0.01),
                  fontsize=18, title='Feature Groups', title_fontsize=18,
                  frameon=False, ncol=1)

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {output_path}")

    # R1 revision: write the pie percentages out, so SI Table S8 and Section 4.7 quote exactly what
    # this figure draws rather than a separately computed set of SHAP values
    shares = {st: {g: round(v, 1) for g, v in d['group_importance'].items()}
              for st, d in shap_data.items()}
    shares['_n_rows_per_stratum'] = SHAP_SAMPLE_SIZE
    side = os.path.splitext(output_path)[0] + '_groups.json'
    json.dump(shares, open(side, 'w'), indent=1)
    print(f"  Group shares: {side}")
    for st, v in shares.items():
        if st.startswith('_'): continue
        print(f"    {st:7s} " + "  ".join(f"{g} {v[g]:.1f}%" for g in
              ['Temporal', 'Geographic', 'Other', 'Radiation', 'Humidity', 'Temperature'] if g in v))
    plt.close()


# =====================================================================
# Main
# =====================================================================
if __name__ == '__main__':
    # Generate new Figure 5 (temp_error target) for main text
    generate_figure(MODEL_PATHS, OUTPUT_FIGURE, xlabel_suffix="temperature error")

    # Generate SI figure (station_temp target)
    generate_figure(MODEL_PATHS_STATION, OUTPUT_FIGURE_SI, xlabel_suffix="model output")

    print("\nDone!")
