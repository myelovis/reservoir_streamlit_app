# Part 4: small steps

This is a local copy of your GitHub app with upgrades. GitHub was only read.
The comments use simple English. There is no Spark, Java or Cassandra setup for the dashboard.

## 1. Open and install

Open this folder in VS Code, then use its terminal:
Use Python 3.11 or 3.12.

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or on Ubuntu / WSL:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

Now enter your credentials **once**:

```bash
python setup_local.py
```

It asks for the full MongoDB URI and ENTSO-E token with hidden input.
They are saved outside the app folder in a private user settings file:

- Windows: `%APPDATA%/NVE_Reservoir_App/secrets.toml`
- Ubuntu/WSL: `~/.config/NVE_Reservoir_App/secrets.toml`

Use the same Windows or WSL environment for setup and the app.
Local app copies, upload scripts and the new notebook reuse this file.
Keep it when updating the app. It is never included in the ZIP or GitHub files.
If credentials change later, edit that private file and restart the app.

## 2. Check the boundaries and points

Already included:

- `data/EL.geojson`: the five price-area boundaries, converted from your shapefile.
- `data/NO.geojson`: their union, used for the mainland national view.
- `data/samples.csv`: exactly **200 points per price area**, **1,000 total**.
- `data/prepared.sqlite3`: the local SQLite database, already holding the 1,000 sample points.
- `geo-nve-atlas_data/`: the original shapefile components.

To repeat the same seeded sampling:

```bash
python prepare_regions.py
```

**VASS is not bundled.** Your repository has no official reservoir-statistics water-area polygons.
The old RS/RØ/RV/RM/RN administrative polygons are not substitutes for VASS.
The NVE area list names four VASS IDs, while the checked published observations contain only three.
The importer therefore requires the official three published areas: VASS1, VASS2 and VASS3.
Do not invent or merge these boundaries from their names.

When you obtain an official file with the correct IDs:

```bash
python prepare_regions.py --water path/to/official_water_areas.shp --water-id YOUR_ID_COLUMN
```

This accepts numbers such as `1`, or codes such as `VASS1`, in the ID column.
It creates `data/VASS.geojson`. The map and weather preparation then use it automatically.
VASS colours and outlines show an informative message until this file is present.

## 3. Fill the local database, then upload it

```bash
python prepare_all_weather.py --year 2024
```

This downloads hourly **ERA5**, with temperature and precipitation, from Open-Meteo.
It writes regional hourly averages into the `hourly` table of `data/prepared.sqlite3`.
This preparation command does not read credentials or write to MongoDB.
It first finds the ERA5 grid cell for each sample. Shared cells are downloaded once.
Compressed local cell files let the next run resume without repeating finished cells.
The first full-year run can take time and may reach the free API limit; resume later if asked.
No API calls are made when the user changes a dashboard control.

To upload the finished local database to Atlas, without calling a weather API:

```bash
python publish_local.py --year 2024
```

It reuses the saved MongoDB URI. It uses **new collections**, so the original 1,000-point NO3 data is kept:

```text
nve
├── era5_samples_v4       # 1,000 unique points across the five price areas
├── era5_hourly_v4        # Regional averages, not every point's hourly data
└── era5_datasets_v4      # Status, year, model, sample count and sample hash
```

Unique indexes and upserts prevent duplicate records. A complete dataset is skipped.
Incomplete datasets can be resumed. The app prefers the new version and falls back to the old
NO3 dataset when the new version is unavailable. The displayed sample count identifies which is used.

If you want to upload only the 1,000 sample coordinates first:

```bash
python publish_local.py --samples-only
```

The dashboard needs the regional weather averages as well to show the new weather plots.

National averages reuse the 1,000 points with price-area-size weights, since equal sample counts
do not make differently sized regions equally large. VASS averages, once its official file is added,
reuse the points falling inside each polygon with those same weights.
VASS sample counts therefore differ from 200. No extra random points are added.
The geographic basis is the price-area sampling frame; this is not a reservoir-capacity-weighted average.

For the free Atlas cluster, only coordinates and regional hourly averages are uploaded.
At 8,784 rows per region in 2024, the new series should use far less than 512 MB, but actual storage
and index size depends on the existing cluster contents. The large per-cell files stay local.

## 4. Run the app

The local app reuses the private file from `setup_local.py`; no repeated credential prompts.
The new pages use the same `nve.reservoir_weekly` publication as your existing app.

```bash
streamlit run app.py
```

The running app only reads prepared Atlas data. It never resamples points, downloads ERA5,
or uploads data when a page or control changes. SARIMAX and Ridge run on those prepared data.
If the reservoir collection has not been published yet, run `python publish_atlas.py --reservoirs` locally once.

For deployment later, add only `MONGO_URI` in Streamlit Cloud Secrets once.
The dashboard does not need the ENTSO-E token because it reads the prepared transfer collection.
For the existing Part 2 download notebook, replace its token-input line with:

```python
from settings import get_secret
token = get_secret("ENTSOE_TOKEN")
```

Run that notebook from this app folder, or add this folder to its Python path.

- **Map**: choose NO, EL or VASS in the sidebar; select colours; click an outlined area.
- **Outliers**: choose a weather property in either tab. Temperature is the default.
- **Correlation**: change the property, lag and window. Positive lag means weather comes first.
- **Forecast**: the shared map time frame is the training period; choose a horizon and model.

SARIMAX uses `(p,d,q)` and optional `(P,D,Q,s)`. Ridge uses past filling values and a penalty.
Both forecast recursively without inserting observed future filling.
Future weather must be an explicit training-based assumption or your uploaded weekly CSV.
The forecast CSV requires `date` plus exactly the selected weather columns, one row per forecast week.
SARIMAX intervals are conditional statistical intervals, not quantile-regression intervals.
Intervals do not include uncertainty in your future-weather assumptions.

The old reservoir and transfer pages are included. Their original data requirements still apply.
The new scripts do not modify Part 2 collections.

For notebook work and tests, install `requirements-dev.txt` in the same environment.
Then run `pytest tests -q` from this folder.

## 5. Run the notebook and write the log

Open `notebooks/Part4_checks.ipynb` after the Atlas datasets are prepared.
Run it from top to bottom. It checks several lags and windows, compares a holdout forecast,
and writes a Markdown log with the actual results.
Do not report the best correlation as proof of prediction: seasonality, small samples and
trying many settings can all create misleading patterns.

The included `WORK_LOG.md` distinguishes implemented features, tested behaviour and checks
that still need your private Atlas connection. No live correlations or prediction scores are invented.

## 6. Files to review

Replace `app.py`, `weather_data.py`, `requirements.txt`, and `pages/4_Weather_Outliers.py`.
The updated `atlas_data.py` and `transfer_data.py` share the saved MongoDB setting.
Add the new helper modules, map, correlation and forecast pages, the preparation scripts,
GeoJSON files, notebook, and tests. The ZIP also contains the existing files for a full local run.
`settings.py`, `setup_local.py`, `local_store.py` and `publish_local.py` handle the one-time setup and local-to-Atlas workflow.

Start with `region_tools.py` and `weather_stats.py`; then read `forecast_tools.py`.
The pages mostly connect these functions to controls.

## Bonus tasks chosen

1. **Waiting time:** cached data and model results, spinners, and preparation progress messages.
2. **Error handling:** database messages, missing boundaries, incomplete weather, NaNs, gaps,
   duplicate dates, invalid parameters, and forecast convergence warnings.

## Sources

- [Your GitHub app](https://github.com/myelovis/reservoir_streamlit_app)
- [NVE API](https://biapi.nve.no/magasinstatistikk/swagger/v1/swagger.json)
- [NVE electricity boundaries](https://kart.nve.no/enterprise/rest/services/Nettomraader/MapServer/0)
- [NVE region definitions](https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOmr%C3%A5der)
- [Open-Meteo historical ERA5](https://open-meteo.com/en/docs/historical-weather-api)
- [Streamlit Folium](https://github.com/randyzwitch/streamlit-folium)
- [Statsmodels SARIMAX forecast](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAXResults.get_forecast.html)
