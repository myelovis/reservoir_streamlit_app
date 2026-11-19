# Norwegian Reservoirs, Weather and Electricity — Part 3

Streamlit dashboard for IND320 parts 1–3.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Set `MONGO_URI` in Streamlit Cloud Secrets or the local environment. Never commit
credentials. The deployed app reads Atlas; page reruns do not upload records or
download weather from Open-Meteo.

## Reuse existing data

The Part 3 app reuses weather already published by Part 4. **The Part 4 branch,
app and stored data remain unchanged.** No re-download or re-upload is needed.

| Shared selection | Weather region ID |
|---|---|
| National NO / 0 | `NO0` |
| Electricity EL / 1–5 | `NO1`–`NO5` |
| Watercourse VASS / 1–3 | `VASS1`–`VASS3` |

Weather reads `nve.era5_datasets_v4` and `nve.era5_hourly_v4` first, using the
existing `era5_{region}_{year}_n200_v4` publication IDs. When a Part 4 publication
does not exist, it checks the original `era5_datasets` / `era5_hourly` publication.
It never substitutes a different region. The original weather-year input is
preserved. Missing data for a selected area/year shows a message.

Part 4's 200 points per electricity area and weighted derived areas are accepted
using their own metadata. The loader checks region, model, publication stability,
complete UTC hours, row count and finite values. Approximate-boundary notes in
metadata are displayed. Part 3's 1,000-per-area constraint is not applied to Part 4.

Reservoirs still read `reservoir_weekly` / `reservoir_datasets`. Electricity
transfers still read `simple_transfers`. The app changes none of these collections.

## Pages and controls

1. Reservoir Overview: table and first-month sparklines.
2. Reservoir Plots: area, month and measurement selection.
3. Reservoir Patterns: STL and spectrogram tabs.
4. Weather Outliers: precipitation DCT/SPC and temperature LOF tabs.
5. Electricity Transfers: NO2–DK1 energy, coverage and power flows.

Area selection is shared between reservoir and weather pages. SPC defaults to a
30-day DCT cutoff and three robust standard deviations estimated over the whole
selected year. LOF defaults to 1% and 20 neighbours. Statistical flags do not prove
data errors. STL uses weekly filling percentages.

## Deployment and tables

Runtime dependencies explicitly include Streamlit, PyArrow and NumPy versions with
Python 3.14 binary wheels. Spark, Cassandra and Jupyter are local coursework tools,
kept out of the cloud environment. Streamlit Cloud rebuilds after requirements
changes; reboot the app in Cloud settings if an old native environment persists.

Tables use scalar schemas and float lists for measurement sparklines. If a native
Arrow import fails during a rebuild, an escaped HTML table provides a readable
fallback, without interactive sorting or sparklines.

## Structure

```text
app.py                         Entry point; deployment path unchanged
pages/                         Part 3 page layouts and controls
reservoir_app/
    atlas.py                   Shared Atlas connection
    areas.py                   Region identities
    reservoirs.py              Reservoir loader, selection and plots
    weather.py                 Existing Part 4 / Part 3 weather loader
    transfers.py               Transfer loader
    analysis.py                STL, spectrogram, SPC and LOF
    transfer_plots.py           Electricity charts
    tables.py                  Formatting and display fallback
scripts/
    era5.py                    Optional original notebook ingestion helper
    publish_atlas.py            Optional notebook reservoir publisher
jupyter notebooks/             Coursework notebook and submitted PDFs
geo-nve-atlas_data/             Original electricity shapefile components
tests/                         Regression tests
requirements.txt               Cloud app dependencies
requirements-notebook.txt      Optional local notebook dependencies
```

Removed legacy files: `reservoirs.csv`, CSV-only `utils.py`, broken
`prepare_weather.py`, notebook checkpoint, and an accidentally committed terminal
diff. Git history retains them. Notebook imports use the new package paths and
find the repository from the notebook folder. Saved outputs are preserved.

Optional scripts never run during normal app operation. Existing Part 4 weather
is reused directly; no ingestion or publishing is needed.

## Checks

```bash
pip install pytest
python -m pytest -q
```

Tests use fixtures, not live database writes. They cover all nine area identities,
Part 4 precedence, Part 3 fallback, invalid/missing weather, Arrow conversion,
native-import fallback, and page rendering with shared area changes.

## Sources

- [NVE Magasinstatistikk](https://biapi.nve.no/magasinstatistikk/swagger/index.html)
- [NVE Atlas](https://atlas.nve.no/)
- [Open-Meteo historical ERA5 data](https://open-meteo.com/en/docs/historical-weather-api)
- [ENTSO-E](https://transparency.entsoe.eu/)
