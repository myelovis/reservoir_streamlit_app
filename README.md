# Norwegian Hydropower Reservoir Dashboard

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
