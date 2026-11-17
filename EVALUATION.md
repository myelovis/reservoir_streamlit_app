# Evaluation

## Completed checks

**19 automated tests passed.** They cover:

- Exactly 200 points in each of the five price areas; every point is inside its region.
- National area weights instead of a simple mean of unequal-sized regions.
- Weekly temperature means, precipitation totals and rejection of partial weeks.
- Positive lag direction and gaps in rolling correlation.
- Temperature defaults and both weather-property controls.
- DCT residuals used internally; only original values, limits and flags are plotted.
- Leap-year hourly data validation, missing data and wrong region IDs.
- SARIMAX future exogenous inputs, recursive Ridge forecasts and animation frames.
- Duplicate-free mock Atlas publication, repeatable sample upload, and an uploader with no weather API calls.
- Shared dates, map-to-sidebar selection and a missing-connection message.
- One-time credentials reused without prompting again or printing secrets.
- SQLite sample/weather round trips, safe sample versions and repeated writes without duplicate rows.
- Main navigation startup and a short training period with no observations.

All Python files and the five notebook code cells were syntax-checked.
The five notebook code cells were also executed with controlled test data, including
24 lag/window combinations and generation of the holdout log. Those test outputs are not bundled as real findings.
The Streamlit page tests use controlled data, not the private Atlas cluster.

## Live checks

- A small ERA5 request succeeded for all five price areas: one sample and one day each.
- Current NVE observations passed the existing loader's validation.
- No live MongoDB writes and no GitHub changes were made.

## Limits to keep visible

1. No official VASS polygon file was available. The app shows a message instead of inventing a boundary.
2. Full new ERA5 regional series must be prepared and uploaded with the user's private connection.
3. A free API quota may stop a first download; saved cells let the next run resume.
4. Forecasts with assumed future weather are scenarios. Historical ERA5 is not a future-weather forecast.
5. Correlation findings and prediction scores must come from the real-data notebook run.

## Simplicity review

- `app.py` is 23 lines and only defines navigation.
- Calculations are in small helper files; pages mostly contain controls and one main chart.
- The preparation script runs outside the app. Slider changes never trigger ERA5 downloads.
- Local preparation writes SQLite; a separate uploader reads SQLite and writes Atlas; the dashboard only reads Atlas.
- Credentials are stored once in the user's private settings folder, outside all shared app files.
- SARIMAX is the statistical model; Ridge is the simple machine-learning alternative.
- The map uses region polygons without a paid tile provider or extra map API key.
- Existing Part 2 collections and the original NO3 dataset are kept separately.

The included SQLite database has a `samples` table with exactly 1,000 rows.
Its `hourly` table will be created when the local ERA5 preparation is run.
Live MongoDB upload and ENTSO-E authentication were not tested without the user's private credentials.

To repeat the checks in a normal Python environment:

```bash
pip install -r requirements-dev.txt
pytest tests -q
```
