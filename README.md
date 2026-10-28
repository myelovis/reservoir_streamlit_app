# Norwegian Hydropower, Weather and Electricity Dashboard

## Part 3: new analysis pages

Navigation is grouped in this order: **Home → Reservoir Overview → Reservoir Plots → Reservoir Patterns → Weather Outliers → Electricity Transfers**. The existing transfer report and its MongoDB configuration are unchanged.

The area selector is shared by the reservoir table, reservoir plots and both new pages. A selection made on Reservoir Plots carries into the analysis pages. Weather currently supports electricity areas **EL 1–5** (NO1–NO5); choosing national or watercourse data shows an explanation rather than substituting another region's weather.

### Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Reservoir Patterns: STL and Spectrogram

This page fetches the selected area's weekly filling series directly from NVE and defaults to the latest five years. Its tabs expose:

- **STL:** seasonal smoother (13), trend smoother (89 weeks), and robust fitting (true). Annual seasonality uses an approximate 52-week period. Plots show observed filling, trend, seasonality and residuals. Components can be downloaded.
- **Spectrogram:** window length (104 weeks) and overlap (78 weeks). The annual frequency is marked at one cycle/year. Spectral power can be downloaded.

At least two years are needed for STL, and at least two full windows for the spectrogram. Missing weeks, duplicate dates, non-finite data and invalid parameters produce an explanatory message; observations are not silently interpolated. Extend the analysis period when needed.

### Weather Outliers: use your completed NO3 notebook download

The fastest route is to reuse your actual **1,000-location NO3, 2024** regional averages. No sample or invented weather dataset is shipped.

Choose **EL → 3 → 2024**, open **Load weather data**, and upload:

```text
weather_fast/NO3_2024-01-01_2024-12-31_1000pts/regional_hourly_mean.csv
```

Alternatively place that file at **data/weather/NO3_2024.csv** in this repository and commit the small CSV on your temporary branch. Existing `weather_fast` folders placed beside `app.py` are also recognised. Files must have columns `time`, `temperature_2m`, `precipitation` and exactly all 8,784 unique UTC hours of 2024 (8,760 for non-leap years). An optional `region_id` column is checked against the selected area. If the column is absent, an upload is explicitly labelled by the user for the selected region/year; its geographic provenance cannot be inferred from weather values alone.

Each region/year has its own file and upload state. There is **no fallback from a missing NO4 dataset to NO3**. Uploads last for the browser session; place exports in `data/weather` to make them available after deployment/restart. Changes to sliders and tabs do not initiate API downloads.

The two weather tabs expose:

- **Precipitation SPC:** cutoff period (30 days), robust standard-deviation multiplier (3), outlier count/share, robust sigma, flagged observations and CSV download. The DCT high-pass residuals (called SATV in the brief) are used internally, not plotted. Median and normal-scaled MAD are estimated from the entire chosen year. Limits are shown in original precipitation units; negative lower limits are statistical boundaries, not negative rainfall.
- **Temperature LOF:** target anomaly proportion (1%), neighbour count (20), actual anomaly count/share, LOF scores and CSV download. The method uses neighbours in temperature-value space, not a seasonally adjusted temporal model. Ties can affect the actual anomaly proportion. Flagged values are not automatically data errors.

### Prepare a missing ERA5 export using the API

The included `era5_module.py` samples 1,000 locations per electricity area, discovers shared ERA5 grid cells, downloads each unique cell's series, and weights cells by sample counts when calculating regional means. Requests explicitly select `models=era5`, UTC, nearest cells, and disable elevation adjustment. Data is cached per region and time interval. It uses the existing electricity shapefile when placed beside the module; otherwise it reads the same official NVE electricity layer directly. Optional local shapefile components are ignored by Git.

Run outside Streamlit for a long download:

```bash
python prepare_weather.py --region NO3 --year 2024
```

This publishes `data/weather/NO3_2024.csv`. On interruption or an API quota failure, rerun to reuse completed cells. Open-Meteo's rate limits apply; long periods and multiple locations count as multiple calls. There is also an explicit **Fetch** button in the weather page for environments able to keep the session running, but a full-year preparation should normally be done before cloud deployment. A five-year reservoir analysis does not require five years of ERA5 data.

### Tests

```bash
pip install pytest
python -m pytest -q tests
```

Tests use clearly labelled synthetic fixtures only. They check STL reconstruction and annual seasonality, an annual spectral peak, an injected precipitation/temperature anomaly, full-year validation, region isolation, both Streamlit tab pages, invalid controls and selector persistence across pages. Synthetic fixtures never feed the running dashboard.

### Sources and attribution

- [NVE Magasinstatistikk API](https://biapi.nve.no/magasinstatistikk/swagger/index.html): reservoir observations.
- [NVE electricity boundary layer](https://kart.nve.no/enterprise/rest/services/Nettomraader/MapServer/0): NO1–NO5 shapefile, downloaded 27 October 2026. Source: Norges vassdrags- og energidirektorat (NVE); [NLOD](https://data.norge.no/nlod/no/). Boundary vintage has not been independently checked for historical changes.
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api): ECMWF ERA5 weather, via Open-Meteo. Attribute Open-Meteo and the ERA5 data source when exporting/sharing results; see its data licences and usage limits.

The branch is intended for peer review before merging into `main`. Setting up the app does not update your existing Streamlit deployment automatically.

---

## Earlier project overview

An interactive, multi-page Streamlit web application for analyzing, visualizing, and inspecting historical reservoir water levels, energy storage capacity (TWh), and fill ratios across Norway's bidding zones.

---

## Features

- **Data Overview (`1_Data_Overview.py`)**:
  - Tabular view of numerical features with summary statistics (Count, Mean, Min, Max).
  - Embedded inline sparklines (`LineChartColumn`) displaying early trend dynamics across the first 30 days.

- **Interactive Visualizations (`2_Interactive_Visualizations.py`)**:
  - Custom date range selection using monthly sliders.
  - Granular single-feature inspection or normalized multi-feature comparison.
  - High-contrast dark theme styling with a sleek black plot canvas.

- **Summary Analytics (`3_Summary_Analytics.py`)**:
  - Publication-quality grid subplots for individual time series metrics with directional delta color fills (inflow/outflow).
  - Dual $y$-axis overlay chart combining total storage/capacity (TWh) and national mean fill ratio on different scales.
  - Dynamic UI theme integration for seamless plot-to-app background blending.

---

## Project Structure

```text
.
├── .devcontainer/              # Development container configuration files
├── pages/                      # Multi-page Streamlit views
│   ├── 1_Reservoir_Table.py    # Reservoir table data page
│   ├── 2_Reservoir_Plots.py    # Reservoir plotting page
│   ├── 3_Electricity_Transfers.py # Electricity transfers page
│   └── technotes.txt           # Technical notes for pages
├── README.md                   # Project documentation
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── reservoir_data.py           # Reservoir data processing modules
├── technote.txt                # General technical notes
├── transfer_data.py            # Data fetching/processing for transfers
├── transfer_plots.py           # Plotting utilities for transfers
└── utils.py                    # Helper functions and shared utilities
