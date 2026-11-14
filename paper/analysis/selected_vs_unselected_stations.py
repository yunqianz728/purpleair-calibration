"""Reviewer 1.2: how do the reference stations we used compare with the ones we did not?

The pairing kept a HadISD station only if a PurpleAir sensor sat within 3 km of it and matched it
on elevation and canopy cover. That selection could have favoured a particular kind of site, which
would limit how far the calibration generalises. This compares the 69 stations that entered the
study against a random sample of the US HadISD stations that did not, on the same NLCD 2021
percent-developed-imperviousness measure used elsewhere in the paper.

The candidate workbook from the original pairing step no longer exists, so the comparison pool is
rebuilt from the published HadISD station inventory rather than from that file. The pool is
therefore "US HadISD stations that are not in the study", which is slightly broader than "stations
that were considered and rejected": it also contains stations with no PurpleAir sensor anywhere
near them. That makes it the more demanding comparison, not the weaker one.

Inputs : the HadISD station inventory (downloaded if absent) and PA_PARQUET for the 69 used stations
Output : <PA_OUT>/selected_vs_unselected_stations.json and .csv
Usage  : PA_PARQUET=... PA_OUT=analysis_R1/results50 python3 analysis_R1/selected_vs_unselected_stations.py
"""
import json, os, re, subprocess, sys, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
PARQUET = os.environ.get('PA_PARQUET', '')
INV = os.path.join(BASE, 'hadisd_station_fullinfo.txt')
URL = 'https://www.metoffice.gov.uk/hadobs/hadisd/v343_2025f/files/hadisd_station_fullinfo_v343_2025f.txt'
N_SAMPLE, SEED = 500, 42
LAYER = 'mrlc_display:NLCD_2021_Impervious_L48'


def inventory():
    if not os.path.exists(INV):
        subprocess.run(['curl', '-s', '-m', '120', '-o', INV, URL], check=True)
    rows = []
    for line in open(INV):
        m = re.match(r'(\S+)\s+(.{1,40}?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)', line)
        if m:
            rows.append((m.group(1), m.group(2).strip(), float(m.group(3)), float(m.group(4)), float(m.group(5))))
    return pd.DataFrame(rows, columns=['id', 'name', 'lat', 'lon', 'elev'])


def impervious(lat, lon):
    """Percent developed imperviousness at a point, from the MRLC public WMS. None on failure."""
    d = 0.0005
    url = ('https://www.mrlc.gov/geoserver/mrlc_display/wms?SERVICE=WMS&VERSION=1.1.1'
           f'&REQUEST=GetFeatureInfo&LAYERS={LAYER}&QUERY_LAYERS={LAYER}&STYLES=&SRS=EPSG:4326'
           f'&BBOX={lon-d},{lat-d},{lon+d},{lat+d}&WIDTH=3&HEIGHT=3&X=1&Y=1&INFO_FORMAT=application/json')
    for _ in range(3):
        try:
            out = subprocess.run(['curl', '-s', '-m', '60', '-A', 'research-analysis', url],
                                 capture_output=True, text=True).stdout
            return json.loads(out)['features'][0]['properties']['PALETTE_INDEX']
        except Exception:
            time.sleep(2)
    return None


def main():
    inv = inventory()
    used = pd.read_parquet(PARQUET, columns=['hadisd_station_id', 'station_lat', 'station_lon']) \
             .groupby('hadisd_station_id').first().reset_index()
    used_ids = set(used['hadisd_station_id'])

    conus = inv[(inv.lat.between(24, 72)) & (inv.lon.between(-180, -66))].copy()
    conus['selected'] = conus['id'].isin(used_ids)
    pool = conus[~conus.selected]
    sample = pool.sample(n=min(N_SAMPLE, len(pool)), random_state=SEED)
    print(f'{len(conus)} US HadISD stations; {int(conus.selected.sum())} of ours matched by id; '
          f'sampling {len(sample)} of the {len(pool)} others', flush=True)

    rows = []
    for grp, frame in [('selected', conus[conus.selected]), ('not selected', sample)]:
        for i, (_, r) in enumerate(frame.iterrows(), 1):
            rows.append({'group': grp, 'id': r['id'], 'name': r['name'], 'lat': r['lat'],
                         'lon': r['lon'], 'elev': r['elev'], 'impervious_pct': impervious(r['lat'], r['lon'])})
            if i % 50 == 0:
                print(f'  {grp}: {i}/{len(frame)}', flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(BASE, 'selected_vs_unselected_stations.csv'), index=False)

    out = {'n_us_hadisd': int(len(conus)), 'n_selected_matched': int(conus.selected.sum()),
           'n_sampled_unselected': int(len(sample)), 'layer': LAYER}
    # The MRLC impervious layer returns palette sentinels outside its coverage (127, 255), which
    # are NoData, not percentages. The L48 layer does not cover Alaska, so the Alaskan stations in
    # both groups come back as sentinels and must be dropped rather than read as 127% impervious.
    d['impervious_pct'] = d['impervious_pct'].where(d['impervious_pct'].between(0, 100))
    out_nodata = {g: int(d.loc[d.group == g, 'impervious_pct'].isna().sum()) for g in d.group.unique()}
    for grp in ['selected', 'not selected']:
        v = d.loc[(d.group == grp) & d.impervious_pct.notna(), 'impervious_pct']
        out[grp] = {'n': int(len(v)), 'median': round(float(v.median()), 1),
                    'mean': round(float(v.mean()), 1),
                    'q1': round(float(v.quantile(.25)), 1), 'q3': round(float(v.quantile(.75)), 1),
                    'pct_above_20': round(100 * float((v > 20).mean()), 1),
                    'pct_below_5': round(100 * float((v < 5).mean()), 1)}
    from scipy.stats import mannwhitneyu
    va = d.loc[(d.group == 'selected') & d.impervious_pct.notna(), 'impervious_pct']
    vb = d.loc[(d.group == 'not selected') & d.impervious_pct.notna(), 'impervious_pct']
    out['no_data_dropped'] = out_nodata
    out['mannwhitney_p'] = round(float(mannwhitneyu(va, vb, alternative='two-sided').pvalue), 3)
    json.dump(out, open(os.path.join(BASE, 'selected_vs_unselected_stations.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
