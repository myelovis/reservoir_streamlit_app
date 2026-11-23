from popup_ui import in_popup, page_title, settings
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from reservoir_data import choose_area, METRICS, reservoir_plot

page_title("Reservoir plots")
series = choose_area()
from popup_ui import uses_home_selection
if uses_home_selection():
    from shared_ui import choose_period
    start, end = choose_period(series)
    series = series.loc[str(start):str(end)]
months = series.index.to_period("M").unique().sort_values().astype(str).tolist()
with settings('Plot settings'):
    if not uses_home_selection():
        first, last = st.select_slider("Months", options=months, value=(months[-min(12, len(months))], months[-1]),
                                        help="Choose which months to plot. The default shows up to the latest twelve months.")
    column = st.selectbox("Measure", [*METRICS, "All measures"],
                          format_func=lambda name: METRICS.get(name, name),
                          help="Choose a measurement in its original units, or use All measures to compare normalized trends.")
periods = series.index.to_period("M")
selected = series if uses_home_selection() else series.loc[(periods >= pd.Period(first)) & (periods <= pd.Period(last))]
if selected.empty:
    st.info("No reported observations in these months.")
    st.stop()
fig = reservoir_plot(selected, column)
st.pyplot(fig)
plt.close(fig)
st.caption("All measures uses min–max scaling over the selected interval; constant measures appear at zero.")
if not uses_home_selection():
    st.caption("The month slider filters the NVE observations displayed.")
