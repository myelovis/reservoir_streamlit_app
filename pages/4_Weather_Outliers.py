from popup_ui import in_popup, page_title, settings
import streamlit as st
import pandas as pd
from reservoir_data import choose_area, METRICS

page_title("Reservoir table")
series = choose_area()
from popup_ui import uses_home_selection
if uses_home_selection():
    from shared_ui import choose_period
    start, end = choose_period(series)
    series = series.loc[str(start):str(end)]
first_month = series.index.min().to_period("M")
month = series.loc[series.index.to_period("M") == first_month]
st.caption(f"First available month: {first_month}. One row per imported field.")
fields = month.reset_index()
table = pd.DataFrame([{
    "Field": METRICS.get(column, column.replace("_", " ").title()),
    "Role": "Measure" if column in METRICS else "Metadata",
    "Latest value": str(fields[column].iloc[-1]),
    "First month": fields[column].tolist() if pd.api.types.is_numeric_dtype(fields[column]) else [],
} for column in fields.columns])
summary_tab, records_tab = st.tabs(['Field summary', 'Records'])
with summary_tab:
    st.dataframe(table, column_config={
        "First month": st.column_config.LineChartColumn("First month")}, hide_index=True, width="stretch")
st.caption("Each numeric field has its own sparkline scale. Dates and text use values; identifiers are metadata.")
with records_tab:
    st.dataframe(month, height=280, width="stretch")
