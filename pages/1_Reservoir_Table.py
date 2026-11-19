import streamlit as st
from reservoir_app.tables import display_dataframe, reservoir_summary
from reservoir_app.reservoirs import choose_area, METRICS

st.title("Reservoir table")
series = choose_area()
first_month = series.index.min().to_period("M")
month = series.loc[series.index.to_period("M") == first_month]
st.caption(f"First available month: {first_month}. One row per imported field.")
table = reservoir_summary(month, METRICS)
display_dataframe(table, column_config={
    "First month": st.column_config.LineChartColumn("First month")}, hide_index=True, width="stretch")
st.caption("Each numeric field has its own sparkline scale. Dates and text use values; identifiers are metadata.")
display_dataframe(month, width="stretch")
