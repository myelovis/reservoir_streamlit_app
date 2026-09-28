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
reservoir_streamlit_app/
├── app.py                          # Main landing page / app entrance
├── utils.py                        # Shared data loader and caching utility functions
├── reservoirs.csv                  # Primary Norwegian reservoir dataset
├── requirements.txt                # Python library dependencies
└── pages/
    ├── 1_Data_Overview.py          # Feature summary table & sparkline trends
    ├── 2_Interactive_Visualizations.py # Custom time-window plot controls
    └── 3_Summary_Analytics.py      # Grid subplots & dual-axis national trend analysis
