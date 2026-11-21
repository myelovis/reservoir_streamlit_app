# Historical dates on Home

Replace the files at the matching locations in your existing app. This package includes the historical weather loader, date selector, Home-popup helpers and the affected reservoir/weather pages. It does not replace `app.py`, your stylesheet or your latest forecast page/model files.

## Install

1. Copy the package into the project root, preserving the `pages/` paths.
2. Commit and push the intended Python files to the branch used by Streamlit.
3. Reboot the Streamlit app to clear its caches.
4. Open Home → Select region and dates. Select an early published weather year, then Done.
5. Open Weather outliers. Use Analysis year to choose a year inside the Home period.

No downloads, sample changes, credentials changes or Atlas publication are needed. Data already published stays unchanged.

## Behaviour

- Home reads the selected region's completed year metadata from `era5_history_v1`, `era5_datasets_v4` and the legacy `era5_datasets` collection. It requests only year labels, not compressed weather payloads.
- Home's allowed dates cover the union of available reservoir dates and published weather years. If your first published weather year is 1996, the calendar begins in 1996. It will not claim 1995 exists unless 1995 is published.
- An interval spanning missing weather years can still be selected. Weather pages report unavailable datasets instead of inventing values.
- Weather outliers can analyse historical weather without reservoir observations in that year. The Analysis year selector lists only published years inside the selected period. SPC/LOF run one year at a time, keeping annual SPC statistics and computation manageable.
- Reservoir table, plots, STL, spectrogram, correlation, autocorrelation and forecasts still require reservoir observations. A period wholly before their coverage shows a clear message. For partial overlap, the app reports the reservoir dates actually available.
- Reservoir table continues to summarise the first month inside the selected dates. Standalone pages retain their own selectors; Home popups keep the single shared selection.
- Electricity transfers retains its independent connection/year/month filters.
- The 2007 start of reservoir data, if that is what the active Atlas publication contains, is not changed. This update enables earlier weather analysis; it does not create earlier reservoir filling measurements.

## Files

```text
analysis_popup.py
history_store.py
popup_ui.py
region_picker.py
reservoir_data.py
shared_ui.py
weather_data.py
pages/1_Reservoir_Table.py
pages/2_Reservoir_Plots.py
pages/3_Reservoir_Patterns.py
pages/4_Weather_Outliers.py
```

The optional test uses synthetic data and mocked database/UI calls:

```bash
python tests/test_historical_dates.py
```

Offline checks do not replace a smoke test of your deployed app and Atlas permissions.
