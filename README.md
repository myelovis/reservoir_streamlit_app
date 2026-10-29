# Norwegian Reservoirs, Weather and Electricity Dashboard

Streamlit project covering Parts 1–3 of IND320 Data til Beslutning.
**All dashboard plot data is read from MongoDB Atlas. No weather CSVs or data folders are required in GitHub.** APIs are used upstream by the notebook/ingestion scripts, not by plot reruns.

## Parts 1–3 and navigation

1. **Home** — project overview and data flow.
2. **Reservoir Overview** — measurement table and first-month sparklines.
3. **Reservoir Plots** — area/month selection and original or normalised measurements.
4. **Reservoir Patterns** — tabs for STL decomposition and the spectrogram.
5. **Weather Outliers** — tabs for precipitation DCT/SPC and temperature LOF.
6. **Electricity Transfers** — the existing Part 2 NO2–DK1 transfer report.

The shared area selection follows the user between reservoir and analysis pages. Weather supports electricity areas NO1–NO5; it never substitutes NO3 for an area with missing data.

## Atlas collections: keep Parts 2 and 3 separate

```text
Cluster0 / nve
    simple_transfers       Part 2: existing electricity transfer records
    era5_samples           Part 3: existing sample coordinates
    era5_hourly            Part 3: existing hourly regional weather averages
    era5_datasets          Part 3: weather publication status and metadata
    reservoir_weekly       NVE weekly reservoir observations
    reservoir_datasets     Reservoir publication status and metadata
```

The app reads its existing `era5_hourly` and `era5_datasets` records. Weather queries require the chosen region, model ERA5 and exact calendar year. The complete publication marker, 1,000 source samples, full-year timestamps, row count and finite values are validated before plotting.

## One-time setup

```bash
pip install -r requirements.txt
```

Configure `MONGO_URI` in Streamlit Cloud **App settings → Secrets**, using your existing full connection URI. Locally use an environment variable or an uncommitted `.streamlit/secrets.toml`:

```toml
MONGO_URI = "mongodb+srv://YOUR_DATABASE_USER:ENCODED_DATABASE_PASSWORD@YOUR_CLUSTER/?authSource=admin"
```

Never commit a real password or connection URI. The deployed app needs read permission on the collections above and Atlas Network Access allowing its connection. The notebook/publisher needs write permission; these may use different database users.

### Publish the NVE reservoir data once

The earlier weather upload does not include reservoir filling observations. To make **STL, spectrogram and the original reservoir plots** read Atlas too, publish the separate NVE dataset:

```bash
python publish_atlas.py --reservoirs
```

It uses `MONGO_URI` from the environment or asks privately for the full URI. It fetches the NVE API, validates it, and upserts reservoir records by area type, area number and observation date. It does not create a full new history on every run. A publication marker prevents reading a partially updated dataset. It does not write to `simple_transfers`, `era5_hourly` or `era5_samples`.

To call it from Jupyter using the URI you already prepared:

```python
from publish_atlas import publish_reservoirs
print("Reservoir records published:", publish_reservoirs(uri))
```

Run this periodically if you want newly published NVE observations. It is not automatically run on every dashboard visit.

### Run Streamlit

```bash
streamlit run app.py
```

For your verified weather data, select **EL → 3 → 2024**. No upload, CSV folder or ERA5 re-download is needed. Refresh buttons clear the short in-memory cache and reread Atlas; they do not write records.

## Analysis controls

- **STL:** weekly filling percentages, approximate 52-week annual cycle, seasonal smoother 13, trend smoother 89, robust mode true; selectable multi-year period and CSV component download.
- **Spectrogram:** window 104 weeks, overlap 78; annual frequency marker and spectral-power download. At least two complete windows are needed.
- **Precipitation SPC:** full-year regional averages, DCT cutoff period 30 days and robust sigma multiplier 3. Median and normal-scaled MAD are estimated from residuals over the entire year. The plot shows original precipitation, boundaries and flagged points; residuals/SATV are not plotted.
- **Temperature LOF:** default target proportion 1%, 20 neighbours; actual counts/share, scores and flagged-data download. Neighbours are in temperature-value space, not seasonal/temporal context.

STL/spectrogram use NVE filling levels. SPC/LOF use ERA5 weather. Statistical flags are not proof of data errors. Missing weeks/hours and invalid parameters are reported rather than silently filled.

## Compact storage for a 512 MB cluster

Store regional averages, not all point-hour combinations:

- NO3, 2024: **8,784 hourly weather records** plus 1,000 coordinate records.
- All five electricity areas for 2024: **43,920 hourly averages** plus 5,000 coordinate records, only if all five have actually been ingested.
- Do not publish the 8,784,000 point-hour rows implied by 1,000 samples per region.
- Upserts and unique indexes avoid duplicate records on retries. The app itself is read-only.
- Check total Atlas usage, including Part 2 collections and indexes. No existing data is automatically deleted.

Only NO3/2024 (AREA = EL > 3) is required. Other regions display a missing-publication message until their own weather data is available in Atlas.

## Files

```text
app.py, reservoir_data.py, atlas_data.py, weather_data.py, analysis.py
publish_atlas.py, era5_module.py, prepare_weather.py
transfer_data.py, transfer_plots.py, requirements.txt
pages/1_Reservoir_Table.py
pages/2_Reservoir_Plots.py
pages/3_Electricity_Transfers.py
pages/4_Reservoir_Patterns.py
pages/5_Weather_Outliers.py
tests/
```

`era5_module.py` and `prepare_weather.py` remain optional upstream tools for missing datasets. They are not imported by the plot loaders and do not run when sliders change. The sampler uses a local electricity shapefile if present, otherwise the official NVE boundary service. No NO1–NO5 weather or shapefile uploads to GitHub are needed for existing Atlas datasets.


## Sources and attribution

- [NVE Magasinstatistikk API](https://biapi.nve.no/magasinstatistikk/swagger/index.html): reservoir observations published upstream to Atlas.
- [NVE Atlas](https://atlas.nve.no/): region boundaries for sampling; NVE/NLOD attribution applies.
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api): ECMWF ERA5 reanalysis, downloaded upstream through the module.
- [ENTSO-E](https://transparency.entsoe.eu/): Part 2 transfer observations, processed through Spark/Cassandra and published to Atlas.

