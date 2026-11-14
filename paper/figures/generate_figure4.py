"""
Figure 4: Spatial error distribution - using Temporal-National model
(a) Map with sensor-level MAE, Köppen climate zones, scale bar, north arrow
(b) Boxplot by Köppen climate zone
Colors matched to Figure 1. Albers Equal Area projection.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
from shapely.geometry import Point
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import warnings
warnings.filterwarnings('ignore')

# ================================
# Configuration
# ================================
# R1 revision: the plotting code below is unchanged. Only the source of `sensor_stats` has moved,
# from the original pickled national model to the predictions of the re-run (analysis_R1/results50),
# and the paths are now overridable so the script does not depend on one machine's Desktop layout.
import os
# The four shapefiles are public downloads; PA_GEO_DIR is where they were unpacked.
#   PA_STATES_SHP  US Census cartographic boundary, states, 1:500k (cb_2024_us_state_500k)
#   PA_KOPPEN_SHP  Koppen-Geiger climate classification polygons
#   PA_RIVERS_SHP  Natural Earth 10m physical, rivers of North America
#   PA_LAKES_SHP   Natural Earth 10m physical, lakes
D = os.environ.get('PA_GEO_DIR', 'data/geo')
PRED = os.environ.get('PA_PRED', 'analysis_R1/results50/pred_Temporal-National__station_temp__National.parquet')
PARQUET = os.environ['PA_PARQUET']
SHAPEFILE_PATH = os.environ.get('PA_STATES_SHP', f'{D}/cb_2024_us_state_500k/cb_2024_us_state_500k.shp')
KOPPEN_SHAPEFILE = os.environ.get('PA_KOPPEN_SHP', f'{D}/Koppen/KoppenClimate.shp')
RIVERS_SHAPEFILE = os.environ.get('PA_RIVERS_SHP', f'{D}/natural_earth_vector/10m_physical/ne_10m_rivers_north_america.shp')
LAKES_SHAPEFILE = os.environ.get('PA_LAKES_SHP', f'{D}/natural_earth_vector/10m_physical/ne_10m_lakes.shp')
OUTPUT_PATH = os.environ.get('PA_FIG_OUT', 'figures/figure4.png')

koppen_colors = {
    'A_Tropical': '#cae9b1',
    'B_Arid': '#77cfb7',
    'C_Temperate': '#40b5c4',
    'D_Continental': '#265daf',
    'E_Polar': '#edfcab'
}

# ================================
# 1. Load and predict
# ================================
print("Loading the re-run predictions...")
df = pd.read_parquet(PARQUET, columns=['sensor_id', 'sensor_lat', 'sensor_lon', 'state',
                                       'MainGroup', 'station temperature'])
pred = pd.read_parquet(PRED)
test = df.loc[pred['row'].values].copy()
test['predicted_station_temp'] = pred['pred'].values

# unweighted, to match Table 2 and the per-zone medians quoted in Section 4.4; the original script
# weighted by Wsample, which made the figure disagree slightly with the text
sensor_stats = test.groupby('sensor_id').agg({
    'sensor_lat': 'first', 'sensor_lon': 'first',
    'state': 'first', 'MainGroup': 'first',
}).reset_index()
sensor_mae = (test.assign(ae=(test['predicted_station_temp'] - test['station temperature']).abs())
                  .groupby('sensor_id')['ae'].mean().reset_index())
sensor_mae.columns = ['sensor_id', 'mae']
sensor_stats = sensor_stats.merge(sensor_mae, on='sensor_id')
sensor_stats['koppen_main'] = sensor_stats['MainGroup']

print(f"Sensors: {len(sensor_stats)}")

# ================================
# 2. Load geographic data
# ================================
print("Loading map data...")
us_states = gpd.read_file(SHAPEFILE_PATH)
us_continental = us_states[~us_states['NAME'].isin(['Alaska', 'Hawaii'])]
us_alaska = us_states[us_states['NAME'] == 'Alaska']
koppen_gdf = gpd.read_file(KOPPEN_SHAPEFILE)
koppen_gdf = koppen_gdf.to_crs('EPSG:4326')
koppen_gdf['geometry'] = koppen_gdf['geometry'].buffer(0)

gdf_stations = gpd.GeoDataFrame(
    sensor_stats,
    geometry=[Point(xy) for xy in zip(sensor_stats['sensor_lon'], sensor_stats['sensor_lat'])],
    crs='EPSG:4326'
)
continental_stations = gdf_stations[~gdf_stations['state'].isin(['Alaska', 'AK', 'Hawaii', 'HI'])]
alaska_stations = gdf_stations[gdf_stations['state'].isin(['Alaska', 'AK'])]

# ================================
# 3. Create figure
# ================================
print("Creating figure...")

albers = ccrs.AlbersEqualArea(central_longitude=-96, central_latitude=37.5,
                               standard_parallels=(29.5, 45.5))
plate = ccrs.PlateCarree()

fig = plt.figure(figsize=(18, 5.5))

# Manual axes: map left, boxplot right, closer
ax_main = fig.add_axes([0.04, 0.08, 0.55, 0.88], projection=albers)
ax_box = fig.add_axes([0.60, 0.15, 0.24, 0.72])

# ===== Panel A: Map =====
ax_main.set_extent([-125, -66, 24, 50], crs=plate)

for main_group, color in koppen_colors.items():
    subset = koppen_gdf[koppen_gdf['MainGroup'] == main_group]
    if len(subset) > 0:
        subset.plot(ax=ax_main, color=color, alpha=0.7, edgecolor='none', zorder=1,
                    transform=plate)

us_continental.boundary.plot(ax=ax_main, linewidth=0.5, color='gray', alpha=0.5, zorder=4,
                              transform=plate)

# Rivers and Lakes - clip to map extent
from shapely.geometry import box as shp_box

# Rivers and Lakes - filter by US boundary intersection
from shapely.geometry import box as shp_box
from shapely.ops import unary_union

us_cont_4326 = us_continental.to_crs('EPSG:4326')
us_cont_4326['geometry'] = us_cont_4326['geometry'].buffer(0)
us_boundary = unary_union(us_cont_4326.geometry).buffer(0.1)

# Rivers (use intersects filter, let cartopy handle the visual clipping via set_extent)
rivers_gdf = gpd.read_file(RIVERS_SHAPEFILE)
if rivers_gdf.crs is not None and str(rivers_gdf.crs) != 'EPSG:4326':
    rivers_gdf = rivers_gdf.to_crs('EPSG:4326')
rivers_gdf = rivers_gdf[rivers_gdf.geometry.notnull()]
rivers_in_us = rivers_gdf[rivers_gdf.intersects(us_boundary)]
if len(rivers_in_us) > 0:
    rivers_in_us.plot(ax=ax_main, color='#FFFFFF', linewidth=0.7, alpha=0.6, zorder=3,
                      transform=plate)

# Lakes (global file has Great Lakes)
lakes_gdf = gpd.read_file(LAKES_SHAPEFILE)
if lakes_gdf.crs is not None and str(lakes_gdf.crs) != 'EPSG:4326':
    lakes_gdf = lakes_gdf.to_crs('EPSG:4326')
lakes_gdf = lakes_gdf[lakes_gdf.geometry.notnull()]
lakes_gdf['geometry'] = lakes_gdf['geometry'].buffer(0)
lakes_in_us = lakes_gdf[lakes_gdf.intersects(us_boundary)]
if len(lakes_in_us) > 0:
    lakes_in_us.plot(ax=ax_main, color='#cce5ff', edgecolor='#99ccff', linewidth=0.5,
                     alpha=0.8, zorder=3, transform=plate)

vmin = gdf_stations['mae'].quantile(0.05)
vmax = gdf_stations['mae'].quantile(0.95)

scatter_main = ax_main.scatter(
    continental_stations.geometry.x, continental_stations.geometry.y,
    c=continental_stations['mae'], cmap='RdYlGn_r', s=120,
    edgecolors='black', linewidths=1, vmin=vmin, vmax=vmax, zorder=5, alpha=0.8,
    transform=plate
)

# Colorbar - below Alaska inset
cbar_ax = fig.add_axes([0.22, 0.06, 0.25, 0.02])
cbar = plt.colorbar(scatter_main, cax=cbar_ax, orientation='horizontal')
cbar.set_label('MAE (°C)', fontsize=14)
cbar.ax.tick_params(labelsize=13)

# No grid, no frame
ax_main.grid(False)
try:
    ax_main.outline_patch.set_visible(False)
except AttributeError:
    ax_main.spines['geo'].set_visible(False)

# (a) label
ax_main.text(0.02, 0.98, '(a)', transform=ax_main.transAxes,
             fontsize=20, fontweight='bold', va='top', ha='left')

# ---- Scale bar at top right ----
sb_start_geo = (-83, 49)
sb_proj_start = albers.transform_point(sb_start_geo[0], sb_start_geo[1], plate)
sb_proj_end = (sb_proj_start[0] + 500000, sb_proj_start[1])

ax_main.plot([sb_proj_start[0], sb_proj_end[0]], [sb_proj_start[1], sb_proj_start[1]],
             'k-', linewidth=4, solid_capstyle='butt', zorder=10)
for x in [sb_proj_start[0], sb_proj_end[0]]:
    ax_main.plot([x, x], [sb_proj_start[1] - 30000, sb_proj_start[1] + 30000],
                 'k-', linewidth=1.5, zorder=12)
ax_main.text(sb_proj_start[0], sb_proj_start[1] - 50000, '0', ha='center', va='top',
             fontsize=11, zorder=12)
ax_main.text(sb_proj_end[0], sb_proj_start[1] - 50000, '500 km', ha='center', va='top',
             fontsize=11, zorder=12)

# ---- North arrow to the RIGHT of scale bar, true north direction ----
na_approx_geo = (-72, 49)
na_p1 = albers.transform_point(na_approx_geo[0], na_approx_geo[1], plate)
na_p2 = albers.transform_point(na_approx_geo[0], na_approx_geo[1] + 2, plate)
dx = na_p2[0] - na_p1[0]
dy = na_p2[1] - na_p1[1]
ln = np.sqrt(dx**2 + dy**2)
arrow_len = 150000
dx_n = dx / ln * arrow_len
dy_n = dy / ln * arrow_len

na_base_x = sb_proj_end[0] + 280000
na_base_y = sb_proj_start[1]

ax_main.annotate('', xy=(na_base_x + dx_n, na_base_y + dy_n),
                 xytext=(na_base_x, na_base_y),
                 arrowprops=dict(arrowstyle='->', lw=2.5, color='black', mutation_scale=15),
                 zorder=10)
ax_main.text(na_base_x + dx_n * 1.2, na_base_y + dy_n * 1.2, 'N',
             ha='center', va='center', fontsize=14, zorder=10)

# ---- Alaska inset ----
ax_inset = fig.add_axes([0.06, 0.12, 0.14, 0.25])
for main_group, color in koppen_colors.items():
    subset = koppen_gdf[koppen_gdf['MainGroup'] == main_group]
    if len(subset) > 0:
        subset.plot(ax=ax_inset, color=color, alpha=0.7, edgecolor='none', zorder=1)
us_alaska.boundary.plot(ax=ax_inset, linewidth=0.5, color='gray', alpha=0.5, zorder=4)
if len(alaska_stations) > 0:
    ax_inset.scatter(
        alaska_stations.geometry.x, alaska_stations.geometry.y,
        c=alaska_stations['mae'], cmap='RdYlGn_r', s=60,
        edgecolors='black', linewidths=0.8, vmin=vmin, vmax=vmax, zorder=5
    )
ax_inset.set_xlim(-180, -130)
ax_inset.set_ylim(51, 72)
ax_inset.set_xticks([])
ax_inset.set_yticks([])
for spine in ax_inset.spines.values():
    spine.set_linestyle('--')
    spine.set_linewidth(1.2)

# ---- Legend (horizontal, bottom right of map, no frame) ----
legend_elements = [
    Patch(facecolor=koppen_colors['A_Tropical'], label='Tropical', alpha=0.85),
    Patch(facecolor=koppen_colors['B_Arid'], label='Arid', alpha=0.85),
    Patch(facecolor=koppen_colors['C_Temperate'], label='Temperate', alpha=0.85),
    Patch(facecolor=koppen_colors['D_Continental'], label='Continental', alpha=0.85),
    Patch(facecolor=koppen_colors['E_Polar'], label='Polar', alpha=0.85)
]
leg = ax_main.legend(handles=legend_elements, loc='center right', fontsize=12,
               frameon=True, facecolor='white', edgecolor='none', framealpha=0.85,
               title='Köppen Climate\nClassifications',
               title_fontsize=13, ncol=1, bbox_to_anchor=(1.05, 0.25))

# ===== Panel B: Boxplot (with frame) =====
koppen_order = ['D_Continental', 'C_Temperate', 'B_Arid']
koppen_labels = ['Continental', 'Temperate', 'Arid']

plot_data = []
plot_labels_list = []
plot_colors_list = []

for i, koppen_group in enumerate(koppen_order):
    data = sensor_stats[sensor_stats['koppen_main'] == koppen_group]['mae']
    if len(data) > 0:
        plot_data.append(data)
        plot_labels_list.append(koppen_labels[i])
        plot_colors_list.append(koppen_colors[koppen_group])

if len(plot_data) > 0:
    bp = ax_box.boxplot(plot_data, labels=plot_labels_list, patch_artist=True, widths=0.6,
                         showmeans=False,  # no mean line
                         boxprops=dict(linewidth=1.5), whiskerprops=dict(linewidth=1.5),
                         capprops=dict(linewidth=1.5),
                         medianprops=dict(color='black', linewidth=2),  # black median
                         showfliers=False)
    for patch, color in zip(bp['boxes'], plot_colors_list):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    # Median value labels on top (black, no unit)
    for i, data in enumerate(plot_data):
        median_val = np.median(data)
        upper_whisker = bp['whiskers'][i*2+1].get_ydata()[1]
        ax_box.text(i+1, upper_whisker + 0.02, f'{median_val:.2f}', ha='center', va='bottom',
                    fontsize=14, fontweight='bold', color='black')

ax_box.set_xlabel('')
ax_box.tick_params(axis='both', labelsize=14)
ax_box.grid(True, axis='y', alpha=0.3)
# Extend y-axis top to fit median labels
ylim = ax_box.get_ylim()
ax_box.set_ylim(ylim[0], ylim[1] + 0.08)

# (b) label
ax_box.text(0.02, 0.98, '(b)', transform=ax_box.transAxes,
            fontsize=20, fontweight='bold', va='top', ha='left')

# Keep frame (box) around subplot (b)
for spine in ax_box.spines.values():
    spine.set_visible(True)

ax_box.set_ylabel('MAE (°C)', fontsize=16)


# ================================
# Save
# ================================
plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Saved: {OUTPUT_PATH}")
plt.close()

print("\nPer-zone statistics:")
for kg in koppen_order:
    data = sensor_stats[sensor_stats['koppen_main'] == kg]['mae']
    if len(data) > 0:
        print(f"  {kg}: n={len(data)}, median={np.median(data):.3f}, mean={np.mean(data):.3f}")
