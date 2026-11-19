"""Download hourly Wi-Fi signal strength (rssi) or barometric pressure for the 98 study sensors.

--field rssi (default) or --field pressure picks the PurpleAir history field; each goes to its own
folder, paper/analysis/<field>/raw. Pressure (hPa, from the sensor's own BME280) answers Reviewer 1's
comment R1.6 the way rssi answers R1.4. The identity and timestamp checks below do not depend on
the field and are run once, into paper/analysis/rssi/.

Reviewer 1 asked whether a device-status signal such as Wi-Fi strength could proxy the internal
heating of the electronics. PurpleAir's history endpoint serves `rssi` for past periods, so this
fetches it for every sensor over the period that sensor contributes to the paired dataset, for the
leave-sensors-out test in rssi_test.py.

Points. The API is billed in points: 2 per history request plus 1 per returned row for `rssi`.
For the 98 sensors this comes to roughly 0.85-0.97 million points. The script reads the balance
from the free /v1/organization endpoint before every sensor and stops before a sensor whose
projected cost would exceed what is left, so it cannot run the balance into the ground halfway
through a request.

The key. Set PURPLEAIR_API_KEY to a READ key in your own shell. The script sends it only to
api.purpleair.com, in the X-API-Key header, and never prints, logs or stores it.

Timestamps. PurpleAir reports a reading at the hour it was taken. The paired dataset advanced every
PurpleAir timestamp by one hour to meet ERA5's end-of-period convention, so a paired row at
time_utc corresponds to the PurpleAir hour time_utc - 1 h. The raw files keep PurpleAir's own
timestamps; rssi_test.py applies the shift when it joins them.

Output: paper/analysis/rssi/raw/<sensor>.csv  (time_stamp [UTC epoch], rssi [dBm]), resumable
        paper/analysis/rssi/fetch_log.csv        one line per request: sensor, window, rows, status
Before the download, two checks establish that what comes back belongs to the right sensor, place
and hour (a few thousand points in all):
  --verify-location  asks the API for every sensor's coordinates and compares them with the
                     sensor_lat/sensor_lon of the paired data, so sensor_id is confirmed to be the
                     PurpleAir sensor_index of the sensor we paired, at the place we paired it.
  --verify-time      fetches temperature for three days at one sensor in each US time zone and
                     compares it, in deg F, with the paired data's sensor temperature at lags of
                     -3..+3 hours. The lag at which the two series agree is the true offset between
                     the API's timestamps and the paired data's; it must be zero for the join used
                     by rssi_test.py.

Usage : (add --field pressure to any of these for pressure)
        python3 paper/analysis/fetch_rssi.py --check            key type, balance and cost estimate
        python3 paper/analysis/fetch_rssi.py --verify-location  sensor identity and position
        python3 paper/analysis/fetch_rssi.py --verify-time      timestamp alignment, per time zone
        python3 paper/analysis/fetch_rssi.py --one 143214       one full-length request: window accepted? real cost
        (--average 360 or 1440 for 6-hour or daily means, e.g. for pressure, which varies slowly)
        python3 paper/analysis/fetch_rssi.py                    the full download (resumes)
"""
import argparse, csv, json, math, os, ssl, sys, time, urllib.error, urllib.parse, urllib.request
import pandas as pd

try:                                   # python.org builds ship without system CA roots
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

HERE = os.path.dirname(os.path.abspath(__file__))
FIELD = 'rssi'                     # set from --field in main()
OUT = os.path.join(HERE, FIELD, 'raw')
LOG = os.path.join(HERE, FIELD, 'fetch_log.csv')
PARQUET = os.environ.get('PA_PARQUET') or os.path.join(HERE, 'train.parquet')
API = 'https://api.purpleair.com/v1'
AVERAGE = 60                       # minutes; matches the hourly paired data (set from --average)
# longest span the history endpoint accepts for each averaging period, in days
MAX_SPAN_DAYS = {60: 14, 360: 90, 1440: 365}
WINDOW_DAYS = MAX_SPAN_DAYS[AVERAGE]
PAUSE = 1.0                        # seconds between requests
POINTS_PER_REQUEST, POINTS_PER_ROW = 2, 1
# points per returned row, by field: measured with --one (pressure: 714 points for 356 rows, 2026-11-18)
ROW_COST = {'rssi': 1, 'pressure': 2}
MARGIN = 20_000                    # stop with this many points still unspent


def key():
    k = os.environ.get('PURPLEAIR_API_KEY', '').strip()
    if not k:
        sys.exit('PURPLEAIR_API_KEY is not set in this shell.')
    return k


def get(path, params=None, retries=5):
    url = API + path + ('?' + urllib.parse.urlencode(params) if params else '')
    req = urllib.request.Request(url, headers={'X-API-Key': key(), 'User-Agent': 'research-download'})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors='replace')
            try:
                body = json.loads(body)
            except ValueError:
                body = {'description': body[:300]}
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            return e.code, body
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise


def remaining_points():
    s, d = get('/organization')
    if s != 200:
        sys.exit(f'/organization returned {s}: {d.get("description") or d}')
    return int(d.get('remaining_points', 0))


def periods():
    """Each sensor's span in the paired data, mapped back to PurpleAir's own clock, with a day of slack."""
    d = pd.read_parquet(PARQUET, columns=['sensor_id', 'time_utc'])
    d['t'] = pd.to_datetime(d.time_utc, utc=True) - pd.Timedelta(hours=1)
    g = d.groupby('sensor_id')['t'].agg(['min', 'max', 'size'])
    g['start'] = (g['min'] - pd.Timedelta(days=1)).map(lambda t: int(t.timestamp()))
    g['end'] = (g['max'] + pd.Timedelta(days=1)).map(lambda t: int(t.timestamp()))
    return g


def windows(start, end):
    step = WINDOW_DAYS * 86400
    w = []
    while start < end:
        w.append((start, min(start + step, end)))
        start += step
    return w


def estimate(g):
    hours = int(((g['end'] - g['start']) / 3600).sum())
    calls = int(sum(len(windows(a, b)) for a, b in zip(g['start'], g['end'])))
    rows = hours * 60 // AVERAGE
    return calls, rows, calls * POINTS_PER_REQUEST + rows * POINTS_PER_ROW


def done_windows(sensor):
    if not os.path.exists(LOG):
        return set()
    with open(LOG) as f:
        return {(int(r['start']), int(r['end'])) for r in csv.DictReader(f)
                if r['sensor'] == str(sensor) and r['status'] == '200'}


def log(sensor, a, b, rows, status, note=''):
    new = not os.path.exists(LOG)
    with open(LOG, 'a', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['sensor', 'start', 'end', 'rows', 'status', 'note'])
        w.writerow([sensor, a, b, rows, status, note])


def fetch(sensor, a, b):
    s, d = get(f'/sensors/{sensor}/history',
               {'start_timestamp': a, 'end_timestamp': b, 'average': AVERAGE, 'fields': FIELD})
    if s != 200:
        return s, [], (d.get('description') or d.get('error') or str(d))[:200]
    f = d.get('fields', [])
    it, ir = f.index('time_stamp'), f.index(FIELD)
    return s, [(r[it], r[ir]) for r in d.get('data', [])], ''


def save(sensor, rows):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f'{sensor}.csv')
    new = not os.path.exists(p)
    with open(p, 'a', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['time_stamp', FIELD])
        w.writerows(rows)


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def verify_location():
    d = pd.read_parquet(PARQUET, columns=['sensor_id', 'sensor_lat', 'sensor_lon'])
    ours = d.groupby('sensor_id')[['sensor_lat', 'sensor_lon']].first()
    rows = []
    for sensor, r in ours.iterrows():
        s, j = get(f'/sensors/{sensor}', {'fields': 'name,latitude,longitude'})
        if s != 200:
            rows.append({'sensor': sensor, 'status': s, 'note': (j.get('description') or str(j))[:120]})
        else:
            api = j['sensor']
            dist = haversine_m(r.sensor_lat, r.sensor_lon, api['latitude'], api['longitude'])
            rows.append({'sensor': sensor, 'status': s, 'lat_paired': r.sensor_lat, 'lon_paired': r.sensor_lon,
                         'lat_api': api['latitude'], 'lon_api': api['longitude'], 'distance_m': round(dist, 1)})
        time.sleep(PAUSE)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, 'rssi', 'verify_location.csv'), index=False)
    ok = out[out.status == 200]
    print(f'{len(ok)} of {len(out)} sensors answered; distance between paired and API position:')
    print(ok.distance_m.describe().round(1).to_string())
    print('sensors more than 100 m apart:', ok[ok.distance_m > 100][['sensor', 'distance_m']].to_dict('records'))
    bad = out[out.status != 200]
    if len(bad):
        print('not answered:', bad[['sensor', 'status', 'note']].to_dict('records'))


def verify_time(days=3):
    d = pd.read_parquet(PARQUET, columns=['sensor_id', 'timezone', 'time_utc', 'sensor temperature'])
    d['t_pa'] = pd.to_datetime(d.time_utc, utc=True) - pd.Timedelta(hours=1)   # PurpleAir's own clock
    d['temp_f'] = d['sensor temperature'] * 9 / 5 + 32
    results = []
    for tz, g in d.groupby('timezone'):
        sensor = g.sensor_id.value_counts().index[0]             # best-covered sensor in this zone
        s_rows = g[g.sensor_id == sensor].sort_values('t_pa')
        t0 = s_rows.t_pa.iloc[len(s_rows) // 2].floor('D')        # a window from the middle of its record
        a, b = int(t0.timestamp()), int((t0 + pd.Timedelta(days=days)).timestamp())
        s, j = get(f'/sensors/{sensor}/history',
                   {'start_timestamp': a, 'end_timestamp': b, 'average': AVERAGE, 'fields': 'temperature'})
        if s != 200:
            results.append({'timezone': tz, 'sensor': sensor, 'status': s}); continue
        f = j['fields']; it, iv = f.index('time_stamp'), f.index('temperature')
        api = pd.Series({pd.Timestamp(r[it], unit='s', tz='UTC'): r[iv] for r in j['data']}).sort_index()
        ours = s_rows.set_index('t_pa')['temp_f']
        best = None
        for lag in range(-3, 4):
            shifted = api.copy(); shifted.index = shifted.index + pd.Timedelta(hours=lag)
            both = pd.concat([shifted.rename('api'), ours.rename('ours')], axis=1, join='inner').dropna()
            if len(both) < 10:
                continue
            mad = float((both.api - both.ours).abs().mean())
            exact = float(((both.api - both.ours).abs() < 0.51).mean())
            rec = {'lag_h': lag, 'n': len(both), 'mean_abs_diff_F': round(mad, 3), 'share_within_0.5F': round(exact, 3)}
            if best is None or mad < best['mean_abs_diff_F']:
                best = rec
        results.append({'timezone': tz, 'sensor': sensor, 'window_start_utc': str(t0), 'status': s, 'best': best})
        print(f'{tz:10s} sensor {sensor}: best match at lag {best["lag_h"] if best else None} h  {best}', flush=True)
        time.sleep(PAUSE)
    json.dump(results, open(os.path.join(HERE, 'rssi', 'verify_time.json'), 'w'), indent=1, default=str)
    lags = {r['best']['lag_h'] for r in results if r.get('best')}
    print('ALIGNED: API time_stamp == time_utc - 1 h in every zone' if lags == {0} else
          f'NOT ALIGNED: best lags {sorted(lags)} -- do not run the join until this is resolved')


def main():
    global FIELD, OUT, LOG, AVERAGE, WINDOW_DAYS, MARGIN, POINTS_PER_ROW
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--verify-location', action='store_true')
    ap.add_argument('--verify-time', action='store_true')
    ap.add_argument('--one', type=int)
    ap.add_argument('--field', choices=['rssi', 'pressure'], default='rssi')
    ap.add_argument('--margin', type=int, default=MARGIN,
                    help='points to leave unspent; the per-sensor check stops before going below it')
    ap.add_argument('--average', type=int, choices=sorted(MAX_SPAN_DAYS), default=60,
                    help='averaging period in minutes; 360 or 1440 cost 1/6 or 1/24 of the hourly points')
    a = ap.parse_args()
    MARGIN = a.margin
    FIELD, AVERAGE = a.field, a.average
    POINTS_PER_ROW = ROW_COST[FIELD]
    WINDOW_DAYS = MAX_SPAN_DAYS[AVERAGE]
    folder = FIELD if AVERAGE == 60 else f'{FIELD}_{AVERAGE}min'   # never mix resolutions in one folder
    OUT, LOG = os.path.join(HERE, folder, 'raw'), os.path.join(HERE, folder, 'fetch_log.csv')
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'rssi'), exist_ok=True)   # the checks write there

    g = periods()
    calls, hours, cost = estimate(g)
    s, k = get('/keys')
    if s != 200:
        sys.exit(f'The key was not accepted ({s}): {k.get("description") or k}')
    left = remaining_points()
    print(f'key type: {k.get("api_key_type")} | points remaining: {left:,}')
    print(f'field {FIELD}, {AVERAGE}-min averages: {len(g)} sensors, {calls:,} requests, up to {hours:,} rows'
          f' -> at most {cost:,} points ({POINTS_PER_ROW} point(s) per row; --one measures the real rate) | output {OUT}')
    if a.check:
        print('enough for the full download' if left - MARGIN >= cost else
              f'NOT enough: short by about {cost + MARGIN - left:,} points')
        return
    if a.verify_location:
        verify_location(); print(f'points left: {remaining_points():,}'); return
    if a.verify_time:
        verify_time(); print(f'points left: {remaining_points():,}'); return

    if a.one:
        # one full-length request: confirms the API accepts the window used for this average, and its cost
        t0 = int(g.loc[a.one, 'start'])
        t1 = min(t0 + WINDOW_DAYS * 86400, int(g.loc[a.one, 'end']))
        before = left
        s, rows, note = fetch(a.one, t0, t1)
        after = remaining_points()
        print(f'sensor {a.one}, {(t1 - t0) / 86400:.0f} days at {AVERAGE} min: status {s}, {len(rows)} rows, '
              f'{before - after} points used {note}')
        print('first rows:', rows[:3])
        return

    for sensor, r in g.iterrows():
        todo = [w for w in windows(int(r.start), int(r.end)) if w not in done_windows(sensor)]
        if not todo:
            continue
        need = len(todo) * POINTS_PER_REQUEST + sum((b - a_) // (60 * AVERAGE) for a_, b in todo) * POINTS_PER_ROW
        left = remaining_points()
        if left - MARGIN < need:
            print(f'stopping before sensor {sensor}: it needs ~{need:,} points, {left:,} remain')
            break
        got = 0
        for a_, b in todo:
            s, rows, note = fetch(sensor, a_, b)
            if s == 200:
                save(sensor, rows)
                got += len(rows)
            log(sensor, a_, b, len(rows), s, note)
            if s in (401, 403) and 'key' in note.lower():
                sys.exit(f'stopped: {note}')
            time.sleep(PAUSE)
        print(f'{sensor}: {got:,} rows over {len(todo)} requests | {remaining_points():,} points left', flush=True)


if __name__ == '__main__':
    main()
