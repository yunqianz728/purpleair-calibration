"""Fetch the two ERA5 products the calibration features are built from.

The paper draws radiation, sensible heat flux and precipitation from ERA5-Land at 0.1 degrees, and
the 10 m wind components from ERA5 single levels at 0.25 degrees. Both are free from the Copernicus
Climate Data Store; this requests exactly the variables, grid, domain and period that were used, so
the reanalysis inputs can be rebuilt from the original source rather than taken on trust.

You do not need this to reproduce the paper's models. The published paired dataset
(data/training_data_with_classification.csv.gz) already carries the sampled values of all six
variables -- u10, v10, ssrd, strd, sshf, tp -- at every one of the 797,744 observations, together
with the wind speed and direction derived from them. This script is for rebuilding those columns
from the gridded archives, or for extending the dataset to other sensors or other dates.

Before running: create a free CDS account, accept the licence for both datasets, and put your key
in ~/.cdsapirc as the CDS documentation describes (https://cds.climate.copernicus.eu/how-to-api).
Requests are queued and the full period is tens of gigabytes, so expect this to take many hours.

Usage: python3 paper/data/download_era5.py [--out DIR] [--start YYYY-MM] [--end YYYY-MM] [--land|--wind]
"""
import argparse
import calendar
import os
import sys

# The ERA5-Land domain of the archived files, read back from them: 457 x 1112 cells at 0.1 degrees,
# covering every US sensor and reference station including Alaska. North/West/South/East.
AREA = [71.4, -178.0, 25.8, -66.9]
START, END = '2022-06', '2024-12'

LAND = dict(
    dataset='reanalysis-era5-land',
    variable=['surface_sensible_heat_flux', 'surface_solar_radiation_downwards',
              'surface_thermal_radiation_downwards', 'total_precipitation'],
    grid=['0.1', '0.1'],
)
WIND = dict(
    dataset='reanalysis-era5-single-levels',
    variable=['10m_u_component_of_wind', '10m_v_component_of_wind'],
    grid=['0.25', '0.25'],
    product_type=['reanalysis'],
)


def months(start, end):
    y, m = (int(v) for v in start.split('-'))
    ey, em = (int(v) for v in end.split('-'))
    while (y, m) <= (ey, em):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='era5')
    p.add_argument('--start', default=START)
    p.add_argument('--end', default=END)
    p.add_argument('--land', action='store_true', help='only the four ERA5-Land variables')
    p.add_argument('--wind', action='store_true', help='only the two ERA5 wind components')
    a = p.parse_args()

    try:
        import cdsapi
    except ImportError:
        sys.exit('cdsapi is not installed:  pip install cdsapi')
    c = cdsapi.Client()

    specs = [s for s, want in ((LAND, a.land or not a.wind), (WIND, a.wind or not a.land)) if want]
    for spec in specs:
        name = 'land' if spec is LAND else 'wind'
        out = os.path.join(a.out, name)
        os.makedirs(out, exist_ok=True)
        for y, m in months(a.start, a.end):
            target = os.path.join(out, f'{y}-{m:02d}.nc')
            if os.path.exists(target):
                print(f'  {target} already here, skipping', flush=True)
                continue
            req = {k: v for k, v in spec.items() if k != 'dataset'}
            req.update(
                year=str(y), month=f'{m:02d}',
                day=[f'{d:02d}' for d in range(1, calendar.monthrange(y, m)[1] + 1)],
                time=[f'{h:02d}:00' for h in range(24)],
                area=AREA, data_format='netcdf',
            )
            print(f'requesting {spec["dataset"]} {y}-{m:02d} -> {target}', flush=True)
            c.retrieve(spec['dataset'], req, target)


if __name__ == '__main__':
    main()
