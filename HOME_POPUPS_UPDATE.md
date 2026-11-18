# Home popups and clearer transfers

## Apply the update

Extract `Home_Popups_Transfer_Update.zip` into your existing app folder. Replace the matching files and keep the `pages` folder in place. The two new helper files, `analysis_popup.py` and `popup_ui.py`, belong beside `app.py`.

Restart Streamlit. On Cloud, commit the changed source files to your deployed branch and reboot the app. No database upload, dependency change or weather download is needed. Your `leaf.jpg` is kept; the app also supports the earlier SVG and does not crash if neither image is available.

## Changes

- All eight arrow buttons on Home open real analysis windows, rather than navigating to another page. The sidebar pages remain available.
- Region and date controls are in a compact popover. Calculations keep their existing settings, cached data and Run buttons.
- Reservoir tables use Summary and Records tabs. Transfer analysis uses Energy, Power flow, and Records & method tabs. Forecasting uses Forecast, Values, and Method tabs.
- Larger settings forms open in popovers; detailed tables are behind tabs or expanders. Popup charts are smaller, with normal scrolling available for unusually long warnings, records or small browser windows. No information is deliberately clipped.
- Imports use dark green solid lines. Exports use light green dashed lines. Export donut segments also have hatching, so direction is not identified by colour alone.
- The source collections and statistical calculations are unchanged. The temporary preview data and credentials are not bundled.

## Verification

Automated checks cover all eight Home windows, submitted forecasts/SPC/STL/spectrogram calculations, existing pages, transfer totals, and distinct line styles and hatching.

**36 automated checks passed** with controlled data. Forecasting and the transfer overview fit without inner scrolling in the tested laptop viewport. Expanded settings, long model warnings and large data tables may require scrolling.

The transfer overview was inspected in a 1366 × 650 viewport and fit without inner scrolling. Power flow and forecast views were also inspected with controlled local data. Detailed views may still need scrolling. These are layout checks, not live-data findings.

No GitHub or Atlas changes were made by Codex. Uploading the files remains your step.
