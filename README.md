# Chronological Insights · direct API edition

Use Python 3.11 or newer. From this folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

For electricity transfers, the app owner sets `ENTSOE_TOKEN` once in Streamlit Community
Cloud under **App settings → Secrets**. Visitors do not enter a token.
An environment variable of the same name is also supported.
For local development, copy `.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml`, replace the placeholder, and keep that private file out of Git.
The reservoir and weather pages require no credentials.

- **Reservoirs:** Streamlit downloads and caches weekly observations from NVE Magasinstatistikk.
- **Weather:** Streamlit requests UTC hourly ERA5 from the Open-Meteo archive. The regional estimate
  is the mean of five reproducible points inside the selected GeoJSON polygon, replacing the earlier
  precomputed Atlas averages. VASS geometries in this branch are approximate.
- **Transfers:** Streamlit requests A11 physical flows from ENTSO-E for the selected NO2–DK1 year.
  The API token is used only for requests to ENTSO-E.
- **Forecasts:** Weather input starts six days before the first Sunday observation so the first
  aggregation has a full Monday–Sunday week.

No MongoDB configuration, publication script, or downloaded observation file is required.
Fetch progress shows request and validation stages. When an API does not report how much
data it has sent, the bar stays on its current stage until the response arrives.

## Deployment smoke test

Start with a fresh Streamlit cache and no MongoDB URI. Choose **EL / NO4** and **2024-01-01 to
2024-12-31**. Check Reservoir plots, Weather map colouring, Weather outliers, and Sliding window
correlation. Then run SARIMAX with Temperature selected and a 40-week history. If you configure an
ENTSO-E token, open Electricity transfers and check that both directions have records and the
annual coverage is sensible.
