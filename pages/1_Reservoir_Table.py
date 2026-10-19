import streamlit as st
import pandas as pd
from reservoir_data import choose_area, METRICS

st.set_page_config(page_title="Reservoir Table", layout="wide")
st.title("Reservoir table")
series = choose_area()
first_month = series.index.min().to_period("M")
month = series.loc[series.index.to_period("M") == first_month]
st.caption(f"First available month: {first_month}. One row per imported field.")
fields = month.reset_index()
table = pd.DataFrame([{
    "Field": METRICS.get(column, column.replace("_", " ").title()),
    "Role": "Measure" if column in METRICS else "Metadata",
    "Latest value": "Not provided" if pd.isna(fields[column].iloc[-1]) else str(fields[column].iloc[-1]),
    "First month": fields[column].tolist() if pd.api.types.is_numeric_dtype(fields[column]) else [],
} for column in fields.columns])
st.dataframe(table, column_config={
    "First month": st.column_config.LineChartColumn("First month")}, hide_index=True, width="stretch")
st.caption("Each numeric field has its own sparkline scale. Dates and text use values; identifiers are metadata.")
st.caption("Sparklines follow observation order; horizontal spacing does not represent elapsed time.")
st.dataframe(month, width="stretch")
