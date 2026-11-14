"""Local Climate Zone at every sensor and station, for Reviewer 1's second comment.

R1 asked for "urban form and urban function ... or at least the Local Climate Zone of the selected
sites as well as the non-selected sites". This samples the global LCZ map of Demuzere et al. (2022)
at each PurpleAir sensor, each reference station we used, and the random sample of US HadISD
stations the pairing did not retain, so the three populations can be compared in the scheme the
reviewer named rather than only through NLCD imperviousness.

The map is a 1.4 GB tiled GeoTIFF on Zenodo. It is read through GDAL's virtual file system, which
fetches only the tiles containing the points we ask for, so nothing is downloaded in bulk.

Input : PA_PARQUET for the sensor and station coordinates, and
        <PA_OUT>/selected_vs_unselected_stations.csv for the non-selected sample
Output: <PA_OUT>/lcz_points.csv and lcz_summary.json
Usage : PA_PARQUET=... PA_OUT=analysis_R1/results50 python3 analysis_R1/lcz_points.py
"""
import json, os, sys, time
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')
PARQUET = os.environ['PA_PARQUET']
URL = os.environ.get('PA_LCZ_TIF',
                     '/vsicurl/https://zenodo.org/records/8419340/files/lcz_filter_v3.tif')

# Demuzere et al. (2022) encoding: 1-10 are built types, 11-17 the natural types A-G
LCZ = {1: 'LCZ 1 compact high-rise', 2: 'LCZ 2 compact mid-rise', 3: 'LCZ 3 compact low-rise',
       4: 'LCZ 4 open high-rise', 5: 'LCZ 5 open mid-rise', 6: 'LCZ 6 open low-rise',
       7: 'LCZ 7 lightweight low-rise', 8: 'LCZ 8 large low-rise', 9: 'LCZ 9 sparsely built',
       10: 'LCZ 10 heavy industry', 11: 'LCZ A dense trees', 12: 'LCZ B scattered trees',
       13: 'LCZ C bush, scrub', 14: 'LCZ D low plants', 15: 'LCZ E bare rock or paved',
       16: 'LCZ F bare soil or sand', 17: 'LCZ G water'}
BUILT = set(range(1, 11))


def main():
    import rasterio
    os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
    os.environ.setdefault('CPL_VSIL_CURL_ALLOWED_EXTENSIONS', '.tif')

    df = pd.read_parquet(PARQUET, columns=['sensor_id', 'sensor_lat', 'sensor_lon',
                                           'hadisd_station_id', 'station_lat', 'station_lon'])
    pts = []
    s = df.groupby('sensor_id').first().reset_index()
    pts += [('sensor', str(r.sensor_id), r.sensor_lon, r.sensor_lat) for r in s.itertuples()]
    t = df.groupby('hadisd_station_id').first().reset_index()
    pts += [('station used', r.hadisd_station_id, r.station_lon, r.station_lat) for r in t.itertuples()]

    f = os.path.join(BASE, 'selected_vs_unselected_stations.csv')
    if os.path.exists(f):
        u = pd.read_csv(f)
        u = u[u.group == 'not selected']
        pts += [('station not used', r.id, r.lon, r.lat) for r in u.itertuples()]
    print(f'sampling {len(pts)} points from the global LCZ map', flush=True)

    # Reading tiles over HTTP fails occasionally, and a batched read loses the whole batch when it
    # does. Sample one point at a time with retries, and checkpoint, so a failure costs one point
    # and a re-run resumes instead of starting over.
    out_csv = os.path.join(BASE, 'lcz_points.csv')
    done = {}
    if os.path.exists(out_csv):
        prev = pd.read_csv(out_csv, dtype={'id': str})
        done = {(r.kind, r.id): r._asdict() for r in prev.itertuples()}
        print(f'  resuming: {len(done)} points already sampled', flush=True)

    rows, t0, failed = [], time.time(), 0
    with rasterio.open(URL) as src:
        for n, (kind, pid, lon, lat) in enumerate(pts, 1):
            if (kind, pid) in done:
                rows.append({k: v for k, v in done[(kind, pid)].items() if k != 'Index'})
                continue
            code = None
            for attempt in range(4):
                try:
                    code = int(next(src.sample([(lon, lat)]))[0]); break
                except Exception:
                    time.sleep(1.5 * (attempt + 1))
            if code is None:
                failed += 1
            rows.append({'kind': kind, 'id': pid, 'lat': lat, 'lon': lon,
                         'lcz_code': code, 'lcz': LCZ.get(code) if code is not None else None,
                         'built': None if code not in LCZ else code in BUILT})
            if n % 50 == 0 or n == len(pts):
                pd.DataFrame(rows).to_csv(out_csv, index=False)      # checkpoint
                print(f'  {n}/{len(pts)}  ({time.time() - t0:.0f}s, {failed} unreadable)', flush=True)

    d = pd.DataFrame(rows)
    d.to_csv(out_csv, index=False)

    out = {}
    for kind, g in d.groupby('kind'):
        ok = g[g.lcz.notna()]
        out[kind] = {'n': int(len(g)), 'n_classified': int(len(ok)),
                     'pct_built': round(100 * float(ok.built.mean()), 1) if len(ok) else None,
                     'top': ok.lcz.value_counts().head(5).to_dict()}
    json.dump(out, open(os.path.join(BASE, 'lcz_summary.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
