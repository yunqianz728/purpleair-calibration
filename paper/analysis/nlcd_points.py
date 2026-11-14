"""NLCD 2021 impervious surface (%) and land-cover class at every PA sensor and HadISD station (MRLC WMS point query)."""
import json, subprocess, time, sys
import pandas as pd
S = sys.argv[1]   # parquet with the paired data
df = pd.read_parquet(S, columns=['sensor_id', 'sensor_lat', 'sensor_lon', 'hadisd_station_id', 'station_name', 'station_lat', 'station_lon', 'MainGroup', 'state'])
sens = df.groupby('sensor_id').first()[['sensor_lat', 'sensor_lon', 'MainGroup', 'state']].reset_index()
stat = df.groupby('hadisd_station_id').first()[['station_name', 'station_lat', 'station_lon']].reset_index()

def q(layer, lat, lon):
    d = 0.0005
    url = ('https://www.mrlc.gov/geoserver/mrlc_display/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo'
           f'&LAYERS={layer}&QUERY_LAYERS={layer}&STYLES=&SRS=EPSG:4326&BBOX={lon-d},{lat-d},{lon+d},{lat+d}'
           '&WIDTH=3&HEIGHT=3&X=1&Y=1&INFO_FORMAT=application/json')
    for k in range(3):
        try:
            out = subprocess.run(['curl', '-s', '-m', '60', '-A', 'research-analysis', url], capture_output=True, text=True).stdout
            return json.loads(out)['features'][0]['properties']['PALETTE_INDEX']
        except Exception:
            time.sleep(2)
    return None

rows = []
for kind, tab, la, lo, key in [('sensor', sens, 'sensor_lat', 'sensor_lon', 'sensor_id'), ('station', stat, 'station_lat', 'station_lon', 'hadisd_station_id')]:
    for _, r in tab.iterrows():
        rows.append({'kind': kind, 'id': r[key], 'lat': r[la], 'lon': r[lo],
                     'impervious_pct': q('NLCD_2021_Impervious_L48', r[la], r[lo]),
                     'nlcd_class': q('NLCD_2021_Land_Cover_L48', r[la], r[lo]),
                     **({'MainGroup': r['MainGroup'], 'state': r['state']} if kind == 'sensor' else {'station_name': r['station_name']})})
        time.sleep(0.3)
pd.DataFrame(rows).to_csv('analysis_R1/results/nlcd_points.csv', index=False)
print('saved', len(rows))
