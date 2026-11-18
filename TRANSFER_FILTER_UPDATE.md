# Compact month filter

Replace these two files in your existing project:

```text
transfer_plots.py
pages/5_Electricity_Transfers.py
```

Restart Streamlit, or commit the two files to the deployed branch and reboot the Cloud app.

- Months opens from a small filter button on the right of the Power flow tab.
- A short caption lists the selected months.
- The chart is taller; its legend sits above the plot instead of covering observations.
- Lines are thinner and the grid is lighter. Import/export colours and line styles stay distinct.
- Inside a popup, connection and year settings are behind a separate button to leave more chart space.

This builds on the Home popup update. Existing data, timestamps, units and calculations are unchanged. No records are aggregated or removed for visual smoothing. The transfer calculation/style check and popup startup check passed with controlled data.
