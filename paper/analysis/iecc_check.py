"""Does the dewpoint split of the Temperate zone agree with the IECC moisture regimes? (Reviewer 2, R2.4)

R2 suggested splitting the Koppen temperate sensors by IECC climate zone (moist "A" against dry "B").
SI Section S9 splits them instead by each sensor's own measured summer dewpoint. This places every
sensor in its county's 2021 IECC zone, from the county map PNNL publishes with its guide to climate
zones by county (PNNL-33270, 2022), and cross-tabulates the two groupings for the 33 temperate sensors
of SI Table S14 (record-quality screen applied, as there).

The map: https://basc.pnnl.gov/sites/default/files/ClimateZoneDataFiles.zip (ClimateZones.shp, county
polygons with fields IECC21 and Moisture21). It is not redistributed here; pass its path.

Output: <PA_OUT>/iecc_check.json and iecc_by_sensor.csv
Usage : PA_OUT=paper/results_wide python3 paper/analysis/iecc_check.py <path/to/ClimateZones.shp>
"""
import json, os, sys
import geopandas as gpd, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('PA_OUT') or os.path.join(HERE, '..', 'results_wide')
PARQUET = os.environ.get('PA_PARQUET') or os.path.join(HERE, 'train.parquet')


def main(shp):
    g = gpd.read_file(shp)[['State', 'Country', 'IECC21', 'Moisture21', 'geometry']]   # 'Country' holds the county
    zone = pd.read_parquet(PARQUET, columns=['sensor_id', 'MainGroup']).groupby('sensor_id').MainGroup.first()
    pts = pd.read_csv(os.path.join(OUT, 'lcz_points.csv'))
    s = pts[pts.kind == 'sensor'].assign(sensor_id=lambda d: d.id.astype(int))
    gs = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs='EPSG:4326').to_crs(g.crs)
    j = gpd.sjoin(gs, g, how='left', predicate='within')[['sensor_id', 'State', 'Country', 'IECC21', 'Moisture21']]
    reg = pd.read_csv(os.path.join(OUT, 'sensor_humidity_regime_split.csv'))
    m = reg.merge(j, on='sensor_id', how='left').rename(columns={'Country': 'county'})
    m['koppen'] = m.sensor_id.map(zone)
    m['iecc'] = m.IECC21.astype('Int64').astype(str) + m.Moisture21.fillna('')
    qc_path = os.path.join(OUT, 'generalization', 'qc_flags.json')
    if not os.path.exists(qc_path):
        qc_path = os.path.join(HERE, '..', 'results_20trials', 'generalization', 'qc_flags.json')
    flagged = set(json.load(open(qc_path))['flagged_sensors'])
    t = m[(m.koppen == 'C_Temperate') & ~m.sensor_id.isin(flagged)]
    agree = ((t.regime == 'Moist') == (t.Moisture21 == 'A'))
    out = {'n_temperate_sensors': int(len(t)),
           'crosstab_regime_by_iecc': pd.crosstab(t.regime, t.iecc).to_dict(),
           'agreement_moist_eq_IECC_A': f'{int(agree.sum())} of {len(t)}',
           'iecc_zones_dry_group': sorted(t[t.regime == 'Dry'].iecc.unique().tolist()),
           'iecc_zones_moist_group': sorted(t[t.regime == 'Moist'].iecc.unique().tolist())}
    m.to_csv(os.path.join(OUT, 'iecc_by_sensor.csv'), index=False)
    json.dump(out, open(os.path.join(OUT, 'iecc_check.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
