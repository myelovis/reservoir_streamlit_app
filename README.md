# Chronological Insights · Norway

```text
Chronological Insights
└── Home
    ├── Select region and dates
    │   └── GeoJSON boundaries → shared area and time range
    │
    ├── Explore
    │   ├── ↗ Reservoir table → NVE → weekly observations
    │   ├── ↗ Reservoir plots → NVE → filling, capacity, and stored energy
    │   ├── ↗ Electricity transfers → ENTSO-E → NO2 ↔ DK1 power and energy
    │   └── ↗ STL and spectrogram → NVE → seasonal patterns in weekly filling
    │
    ├── Diagnose
    │   ├── ↗ Weather outliers → Open-Meteo → unusual temperature or rainfall hours
    │   ├── ↗ ACF and PACF → NVE → links between current and past filling
    │   └── ↗ Sliding window correlation → Open-Meteo + NVE → weather and filling links over time
    │
    └── Forecast
        └── ↗ Reservoir forecast → NVE + optional Open-Meteo weather
            └── SARIMAX, Ridge, or Boosting → animated weekly forecast
```

**Data structure in one line:** GeoJSON defines the areas, NVE provides weekly reservoir records, Open-Meteo provides hourly weather, and ENTSO-E provides electricity-flow intervals.

## APIs at a glance

| Source | Request | Data returned | Access |
|---|---|---|---|
| NVE Magasinstatistikk | `GET /magasinstatistikk/api/Magasinstatistikk/HentOffentligData` | JSON records of weekly reservoir observations. The app filters by area and date after download. | Public |
| Open-Meteo Historical Weather API | `GET /v1/archive` with coordinates, start and end dates, hourly properties, `models=era5`, and `timezone=GMT` | Hourly temperature and precipitation for five repeatable sample points inside the selected polygon. The app averages the points at each hour. | Public |
| ENTSO-E Transparency Platform | `GET /api` with `documentType=A11`, bidding-zone codes, and UTC start and end times | XML time series for physical electricity flows. The app requests imports and exports separately. | `ENTSOE_TOKEN` in Streamlit Secrets |

[NVE API](https://biapi.nve.no/magasinstatistikk/swagger/index.html) · [Open-Meteo archive documentation](https://open-meteo.com/en/docs/historical-weather-api) · [ENTSO-E API documentation](https://transparencyplatform.zendesk.com/hc/en-us/articles/15692855254548-Sitemap-for-Restful-API-Integration)

Streamlit fetches observations at runtime and caches validated results. The API-backed pages run without a MongoDB connection. The green progress bar shows completed stages of the load. During a request, it can stay at the current stage until the provider responds.

## Explore

| Home arrow | Inputs | Output |
|---|---|---|
| ↗ **Reservoir table** | NVE weekly rows for the selected area and dates | A first-month summary and underlying reservoir observations. |
| ↗ **Reservoir plots** | NVE filling fraction, capacity, stored energy, previous filling, and weekly change | A weekly time series for the chosen measure. **All measures** scales each series separately for comparison. |
| ↗ **Electricity transfers** | ENTSO-E physical flows in both directions between NO2 (Norway) and DK1 (western Denmark), for the selected year | Annual energy in MWh, reporting coverage, monthly power plots in MW, and interval records. Year and month selections follow Europe/Oslo time. |
| ↗ **STL and spectrogram** | Consecutive weekly NVE filling percentages | STL separates observed filling into trend, seasonal movement, and residuals. It accepts 48 consecutive weeks and uses a 24-week cycle for 48–103 weeks, or a 52-week cycle from 104 weeks onward. The spectrogram shows how the strength of repeating patterns changes over time. |

## Diagnose

| Home arrow | Inputs | Output |
|---|---|---|
| ↗ **Weather outliers** | Hourly ERA5 temperature or precipitation for one analysis year | DCT / SPC and Local Outlier Factor (LOF) flag unusual hours for review. Plots show the overlap with the shared dates. |
| ↗ **ACF and PACF** | Weekly NVE filling percentages or weekly filling changes | Autocorrelation and partial autocorrelation plots show how filling relates to earlier weeks. |
| ↗ **Sliding window correlation** | Open-Meteo weather aggregated to weeks and joined to NVE filling percentage or weekly filling change | Rolling Pearson correlation with a selectable weather lead and window length. Positive lead means weather comes first. Incomplete weather weeks are excluded. |

## Forecast

| Home arrow | Inputs | Output |
|---|---|---|
| ↗ **Reservoir forecast** | Weekly NVE filling percentages from the selected area and date range. Temperature and precipitation from Open-Meteo are optional inputs. | Recursive forecasts from **SARIMAX**, **Ridge regression**, or **Boosting**. View the animated forecast, holdout errors, and prediction values. |

The forecast settings control training history, holdout length, and the future horizon. With weather inputs enabled, the app loads all seven days of weather for the first training week. For future weeks, weather is supplied by the **Recent mean** or **Training seasonal mean** scenario, or by a CSV with a `date` column and the selected weather fields. The forecast is conditional on that scenario. Holdout scores compare the model with a baseline that repeats the last observed filling level.

## Data structure

| Dataset | Row or feature key | Main fields and units |
|---|---|---|
| Reservoir observations | `area_type` + `area_number` + `date_id` | `fill_ratio` and `fill_ratio_previous_week` are fractions. `fill_ratio_change` is a fraction difference. `capacity_twh` and `storage_twh` are in TWh. Analysis pages multiply filling by 100 to display percent. |
| Regional hourly weather | UTC `time` index within the selected region | `temperature_2m` in °C and `precipitation` in mm. Weeks end Sunday. Weekly temperature is the mean and weekly precipitation is the sum. A complete week needs 168 hourly values. |
| Power-flow intervals | `connection` + `direction` + UTC `time` | `direction` is `in` or `out` from Norway’s perspective. `power_mw` × `hours` gives `energy_mwh`. Missing intervals are reflected in coverage. |
| Map boundaries | GeoJSON feature `area_id` | `area_type`, `area_number`, `name`, and polygon geometry. Files are `data/NO.geojson` (national), `data/EL.geojson` (electricity price areas), and `data/VASS.geojson` (water areas). The VASS boundaries are approximate. |

The GeoJSON files provide shapes for the map and sampling locations for weather requests. They contain geometry and area labels. The reservoir and weather selectors share the area ID and date range saved in Streamlit session state.

### Where to find the code

- [Home and navigation](app.py) and [region and date picker](region_picker.py)
- [NVE loader](reservoir_data.py), [Open-Meteo loader](weather_data.py), and [ENTSO-E loader](transfer_data.py)
- [Weather analysis and weekly alignment](weather_stats.py) and [forecast validation](forecast_validation.py)

## Run locally

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Note for Future-self
For **Electricity transfers**, set `ENTSOE_TOKEN` in Streamlit Community Cloud under **App settings → Secrets**. For local use, put the same TOML line in `.streamlit/secrets.toml` or set the environment variable. Keep the real token out of Git.

```toml
ENTSOE_TOKEN = "your-token"
```
