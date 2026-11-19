"""Building height, tree height and population around every sensor and station (Reviewer 1, R1.2).

R1 asked for "urban form and urban function (surface cover fraction, urban morphology, building
height, tree height, human activity) or at least the Local Climate Zone" of the selected and the
non-selected sites. Surface cover (NLCD imperviousness) and LCZ are in SI Section S11; this adds the
other three from global open data, at the same 667 points (98 sensors, the 69 reference stations
used, and the random sample of 500 US HadISD stations not retained):

  building height  GHSL GHS-BUILT-H R2023A, average gross building height 2018, 100 m (Pesaresi et
                   al., 2023), mean over the 3 x 3 cells (300 m) around the point
  population       GHSL GHS-POP R2023A, residents 2020, 100 m (Schiavina et al., 2023), the same 3 x 3
                   cells, as persons per km2
  tree height      Meta / WRI global canopy height map, 1 m (Tolan et al., 2024), within 100 m of the
                   point: share of the area under canopy of at least 2 m, and the mean height of
                   that canopy

All three are read over HTTP through GDAL's virtual file system: only the blocks covering each point
are fetched, nothing is downloaded in bulk. Points are sampled one at a time with retries and
checkpointed, so a failed read costs one point and a re-run resumes.

Input : <PA_OUT>/lcz_points.csv (the 667 points and their coordinates)
Output: <PA_OUT>/urban_form_points.csv and urban_form_summary.json
Usage : PA_OUT=paper/results_wide python3 paper/analysis/urban_form_points.py
"""
import json, math, os, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, '..', 'results_wide')
GHSL = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL'
BUILT_H = GHSL + '/GHS_BUILT_H_GLOBE_R2023A/GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_54009_100/V1-0/tiles/' \
                 'GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_54009_100_V1_0_R{r}_C{c}'
POP = GHSL + '/GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_54009_100/V1-0/tiles/' \
             'GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R{r}_C{c}'
CHM = 'https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/chm/{q}.tif'
CANOPY_MIN, RADIUS = 2.0, 100.0          # m


def ghsl_tile(x, y):
    """GHSL R2023A tiles are 1,000 km squares in World Mollweide, numbered from the top left."""
    return math.floor((9_000_000 - y) / 1_000_000) + 1, math.floor((x + 18_041_000) / 1_000_000) + 1


def quadkey(lon, lat, z=9):
    s = math.sin(math.radians(lat)); fx = (lon + 180) / 360; fy = 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)
    tx, ty = int(fx * 2 ** z), int(fy * 2 ** z)
    return ''.join(str(((tx >> (i - 1)) & 1) + 2 * ((ty >> (i - 1)) & 1)) for i in range(z, 0, -1))


def main():
    import rasterio, pyproj
    from rasterio.windows import Window, from_bounds
    os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
    os.environ.setdefault('CPL_VSIL_CURL_ALLOWED_EXTENSIONS', '.tif,.zip')
    to_mw = pyproj.Transformer.from_crs('EPSG:4326', 'ESRI:54009', always_xy=True)
    to_wm = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)

    pts = pd.read_csv(os.path.join(BASE, 'lcz_points.csv'))[['kind', 'id', 'lat', 'lon']]
    out_csv = os.path.join(BASE, 'urban_form_points.csv')
    done = pd.read_csv(out_csv) if os.path.exists(out_csv) else pd.DataFrame()
    have = set(zip(done.get('kind', []), done.get('id', []).astype(str))) if len(done) else set()
    rows = done.to_dict('records')
    cache = {}

    def ghsl_mean3(template, x, y):
        r, c = ghsl_tile(x, y)
        name = template.format(r=r, c=c)
        p = f'/vsizip//vsicurl/{name}.zip/{os.path.basename(name)}.tif'
        if p not in cache:
            cache[p] = rasterio.open(p)
        d = cache[p]
        row, col = d.index(x, y)
        a = d.read(1, window=Window(col - 1, row - 1, 3, 3), boundless=True, fill_value=0).astype(float)
        a[a < 0] = 0                                     # nodata (-1 / -200) outside built or populated land
        return float(a.mean())

    def canopy(lon, lat):
        u = '/vsicurl/' + CHM.format(q=quadkey(lon, lat))
        with rasterio.open(u) as d:
            x, y = to_wm.transform(lon, lat)
            r = RADIUS / math.cos(math.radians(lat))     # ground metres in Web Mercator units
            a = d.read(1, window=from_bounds(x - r, y - r, x + r, y + r, d.transform), boundless=True,
                       fill_value=0).astype(float)
        cover = a >= CANOPY_MIN
        return float(cover.mean()), (float(a[cover].mean()) if cover.any() else 0.0)

    for i, p in enumerate(pts.itertuples()):
        if (p.kind, str(p.id)) in have:
            continue
        rec = {'kind': p.kind, 'id': p.id, 'lat': p.lat, 'lon': p.lon}
        x, y = to_mw.transform(p.lon, p.lat)
        for key, fn in [('building_height_m', lambda: ghsl_mean3(BUILT_H, x, y)),
                        ('population_per_km2', lambda: 100 * ghsl_mean3(POP, x, y)),
                        ('canopy', lambda: canopy(p.lon, p.lat))]:
            for attempt in range(4):
                try:
                    v = fn()
                    if key == 'canopy':
                        rec['canopy_cover_share'], rec['canopy_height_m'] = v
                    else:
                        rec[key] = v
                    break
                except Exception as e:                   # transient HTTP errors: retry, then record a gap
                    if attempt == 3:
                        rec[f'{key}_error'] = str(e)[:120]
                    time.sleep(3 * (attempt + 1))
        rows.append(rec)
        if (i + 1) % 25 == 0 or i + 1 == len(pts):
            pd.DataFrame(rows).to_csv(out_csv, index=False)
            print(f'{i + 1}/{len(pts)} points', flush=True)
    df = pd.DataFrame(rows); df.to_csv(out_csv, index=False)

    from scipy.stats import mannwhitneyu
    cols = ['building_height_m', 'population_per_km2', 'canopy_cover_share', 'canopy_height_m']
    summ = {'n': df.groupby('kind').size().to_dict(),
            'missing': {c: int(df[c].isna().sum()) for c in cols if c in df},
            'median': {c: df.groupby('kind')[c].median().round(3).to_dict() for c in cols},
            'q25_q75': {c: {k: [round(float(v.quantile(.25)), 3), round(float(v.quantile(.75)), 3)]
                            for k, v in df.groupby('kind')[c]} for c in cols},
            'used_vs_not_used_p': {}, 'sensors_vs_stations_used_p': {}}
    for c in cols:
        a, b, s = (df.loc[df.kind == k, c].dropna() for k in ['station used', 'station not used', 'sensor'])
        summ['used_vs_not_used_p'][c] = round(float(mannwhitneyu(a, b).pvalue), 4)
        summ['sensors_vs_stations_used_p'][c] = float(f'{mannwhitneyu(s, a).pvalue:.2g}')
    json.dump(summ, open(os.path.join(BASE, 'urban_form_summary.json'), 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
