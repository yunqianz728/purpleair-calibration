# Data

The paired dataset behind the paper: every PurpleAir reading matched to a HadISD reference
observation, with the reanalysis fields and all 63 engineered features already joined on.

| File | What it is | Rows |
|---|---|---|
| `training_data_with_classification.csv.gz` | the paired hourly dataset, 99 columns | 797,744 |

**Where it is.** The file is 161 MB, too large to live in the repository itself, so it is attached
to the release rather than committed. Download it from the latest release on the
[releases page](https://github.com/yunqianz728/purpleair-calibration/releases) and put it here:

```bash
gh release download --pattern 'training_data_with_classification.csv.gz' --dir data
shasum -a 256 data/training_data_with_classification.csv.gz
# b6ff674dbd6154066682d8483cc973f533742ea398372bfce0a7f460a9e95c28
```

`pandas.read_csv("data/training_data_with_classification.csv.gz")` reads it compressed. The
evaluation code in [`../paper/`](../paper/README.md) expects it at exactly this path.

## How it was built

98 PurpleAir sensors across 31 states paired with 69 HadISD reference stations, on three criteria:
within 3,000 m, elevation difference within 20 m, canopy-cover difference within 20%. Quality
control and the subsequent time alignment reduce 827,446 matched records to the 797,744 here; the
manuscript's Section 2.1 accounts for every removal. PurpleAir timestamps are shifted forward one
hour so that an instantaneous reading lines up with the end-of-period convention of the ERA5
accumulations.

Mean raw bias, sensor minus station, is **5.417 °C** over the whole dataset.

## Columns

| Column | Meaning |
|---|---|
| `sensor temperature` / `station temperature` | PurpleAir and HadISD temperature (°C) |
| `temp_error` | station − sensor (°C) |
| `hour`, `month` | local standard time, after the one-hour shift described above |
| `MainGroup` | Köppen group: `B_Arid`, `C_Temperate`, `D_Continental` |
| `Temperature class` | `Cold` / `Normal` / `Hot`, from zone-specific 25th and 75th percentiles |
| `life` | sensor age in days since deployment (5–1072) |
| `distance`, `delta_elev`, `delta_tcc` | sensor–station distance (m, ≤3000), elevation and canopy-cover differences |
| `Wsample` | sample weight |
| `ssrd`, `strd`, `sshf`, `tp` | ERA5-Land (0.1°) accumulations converted to hourly values |
| `u10`, `v10`, `wind_speed`, `wind_direction` | ERA5 single levels (0.25°), and the speed and direction derived from them |
| `station_name`, `hadisd_station_id` | reference station (57 of the 69 are airport or airfield stations) |

The remaining columns are the lagged, rolling and interaction terms listed in Table 1 of the paper.

## Reanalysis provenance

Two products, at two resolutions, which is worth stating plainly because a single "ERA5" label
would be wrong:

- **ERA5-Land, 0.1°** — `ssrd`, `strd`, `sshf`, `tp`
- **ERA5 single levels, 0.25°** — `u10`, `v10`

Both are free from the Copernicus Climate Data Store. [`../paper/data/download_era5.py`](../paper/data/download_era5.py)
requests exactly what was used, for anyone rebuilding these columns from the gridded archives or
extending the dataset. Reproducing the paper's models needs none of that: the sampled values are
already columns here.

## Source data

- PurpleAir — <https://www2.purpleair.com/> (API)
- HadISD — <https://www.metoffice.gov.uk/hadobs/hadisd/>
- ERA5 and ERA5-Land — <https://cds.climate.copernicus.eu/>
