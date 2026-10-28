# Norwegian Reservoirs, Weather and Electricity Dashboard

Streamlit application for the IND320 Data til Beslutning project,
combining work from Parts 1, 2 and 3.

The dashboard explores Norwegian reservoir filling, electricity transfers,
and weather patterns using NVE, ENTSO-E and ERA5 data.

## Project Parts

### Part 1 — Reservoir Exploration

The reservoir pages provide:

- Tables of reservoir measurements and metadata.
- Sparklines for numerical measurements in the first available month.
- Selection of national, electricity-area or watercourse data.
- Interactive filtering by month.
- Individual measurements or combined, min–max-scaled plots.

Reservoir measurements include filling fraction, capacity, stored energy,
previous-week filling and weekly filling change.

The original reservoir pages display filling as a fraction:
**0.60 means 60%**. The Part 3 decomposition displays percentages.

### Part 2 — APIs and Electricity Transfers

Reservoir observations are retrieved directly from the NVE
Magasinstatistikk API.

Electricity-transfer data follows the project pipeline:

**ENTSO-E → Spark → Cassandra → Spark → MongoDB → Streamlit**

Data preparation and publication take place outside the dashboard.
Streamlit reads the published transfer results from MongoDB.

The Electricity Transfers page provides:

- Import/export energy summaries.
- Annual transfer visualisation.
- Power-flow plots for the selected period.
- Coverage of the Norway NO2–Denmark DK1 connection.

Imports and exports represent exchanged electricity, not domestic production.

### Part 3 — Weather and Time-Series Analysis

#### Spatial Sampling and ERA5

The ERA5 module:

1. Selects an electricity area from the NVE boundary data.
2. Samples 1,000 reproducible locations uniformly by area.
3. Retrieves hourly historical ERA5 temperature and precipitation
   through Open-Meteo.
4. Reuses weather series when multiple locations share an ERA5 grid cell.
5. Calculates regional averages weighted by sample counts.
6. Saves completed downloads so interrupted runs can resume.

The required test dataset is **NO3, full-year 2024**:
8,784 hourly observations because 2024 is a leap year.

Spatial sampling, regional grouping, maps and detailed analysis are also
documented in the project notebook. The East/West/North grouping follows
the assignment's mapping:

- East = RS + RØ
- West = RV
- North = RM + RN

These are merged NVE administrative polygons. They are distinct from
the electricity areas NO1–NO5.

#### Reservoir Patterns Page

Two tabs analyse weekly NVE reservoir filling data:

| Tab | Analysis | Default controls |
|---|---|---|
| STL decomposition | Observed filling, trend, seasonal component and residuals | Seasonal smoother 13; trend smoother 89; robust fitting enabled |
| Spectrogram | Changes in periodic behaviour over time | Window 104 weeks; overlap 78 weeks |

An approximate 52-week annual cycle is used. The analysis period is
selectable, and missing weeks are reported rather than silently filled.

#### Weather Outliers Page

Two tabs analyse full-year hourly ERA5 regional averages:

| Tab | Analysis | Default controls |
|---|---|---|
| Precipitation SPC | DCT high-pass filtering and robust SPC boundaries | Cutoff period 30 days; multiplier 3 robust standard deviations |
| Temperature LOF | Local Outlier Factor anomaly detection | Target anomaly proportion 1%; 20 neighbours |

Both tabs provide plots, counts, percentages, flagged observations
and CSV downloads.

Filtered precipitation residuals are used internally to calculate
boundaries and identify outliers. They are **not plotted**.

LOF compares neighbours in temperature-value space; it does not explicitly
model seasonal or temporal context. Flagged observations are not
automatically data errors.

## Navigation

1. Home
2. Reservoir Overview
3. Reservoir Plots
4. Reservoir Patterns
   - STL decomposition
   - Spectrogram
5. Weather Outliers
   - Precipitation SPC
   - Temperature LOF
6. Electricity Transfers

The area selection is shared across the reservoir and analysis pages.
Weather analysis currently supports electricity areas NO1–NO5.
Missing weather for another area is not replaced with NO3 data.

## Repository Structure

```text
app.py
reservoir_data.py
analysis.py
weather_data.py
era5_module.py
prepare_weather.py
transfer_data.py
transfer_plots.py
requirements.txt

pages/
    1_Reservoir_Table.py
    2_Reservoir_Plots.py
    3_Electricity_Transfers.py
    4_Reservoir_Patterns.py
    5_Weather_Outliers.py

data/
    weather/
        NO3_2024.csv

tests/
    test_analysis.py
    test_pages.py
```

The weather CSV must be supplied from the completed notebook download
or generated using the preparation command below.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Add the Completed NO3 Weather Data

Copy:

```text
weather_fast/NO3_2024-01-01_2024-12-31_1000pts/regional_hourly_mean.csv
```

to:

```text
data/weather/NO3_2024.csv
```

The CSV must contain:

```text
time,temperature_2m,precipitation
```

An optional `region_id` column is checked against the selected area.

The app validates that the file contains all unique consecutive UTC hours
of the selected year, finite weather values and non-negative precipitation.

Alternatively, upload the CSV through **Load weather data** on the
Weather Outliers page. Select **EL → 3 → 2024** for the NO3 export.
Uploads are session-specific; a committed CSV remains available
after deployment.

## Prepare Weather Data Through the API

For a missing dataset:

```bash
python prepare_weather.py --region NO3 --year 2024
```

This generates:

```text
data/weather/NO3_2024.csv
```

The module uses the electricity shapefile when available beside it.
Otherwise, it retrieves the official NVE electricity polygons directly.

Long downloads are best run outside Streamlit. An explicit Fetch button
is also available in the weather page. API quotas apply, and changing
plot controls does not automatically start another download.

## Streamlit Deployment

- Use `app.py` as the entry point.
- Install dependencies from `requirements.txt`.
- Include the completed regional weather CSV for immediate weather plots.
- Configure `MONGO_URI` in Streamlit Secrets for the transfer page.
- Keep changes on a temporary branch until the required peer review
  and feedback are completed.

Never commit passwords, `.env`, or `.streamlit/secrets.toml`.
The large raw `weather_fast/` directory does not need to be uploaded;
the regional-average export is sufficient for the weather analyses.

## Tests

```bash
pip install pytest
python -m pytest -q tests
```

Tests cover:

- STL reconstruction and annual seasonality.
- Detection of an annual spectral peak.
- Injected precipitation and temperature anomalies.
- Full-year weather validation and region isolation.
- Streamlit tabs, controls and shared area selection.

Test fixtures are synthetic and are never used as dashboard data.

## Data Sources and Attribution

- [NVE Magasinstatistikk](https://biapi.nve.no/magasinstatistikk/swagger/index.html):
  reservoir observations.
- [NVE Atlas](https://atlas.nve.no/):
  geographic boundaries.
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api):
  hourly ECMWF ERA5 reanalysis.
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/):
  electricity-transfer observations.

Acknowledge NVE, Open-Meteo, ECMWF ERA5 and ENTSO-E when presenting
their data, and follow the applicable licences and API usage conditions.

The project notebook contains the work log, methodological assumptions,
analysis results and AI-use documentation.

## Local Database Solution

Publish the completed NO3 ERA5 regional averages to MongoDB Atlas so
Streamlit can load them without CSV files in GitHub.
