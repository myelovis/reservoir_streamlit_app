import streamlit as st
import pandas as pd
from reservoir_data import choose_area, METRICS

st.set_page_config(page_title="Megasinstatistikk Data Overview", layout="wide")
st.title("Megasinstatistikk Data Overview")
series = choose_area().sort_index()
latest_date = series.index.max()
latest_month = latest_date.to_period("M")
month = series.loc[series.index.to_period("M") == latest_month]
st.caption(f"Latest available observation: {latest_date:%d %B %Y}. Sparklines show {latest_month}.")
st.caption("NVE publishes weekly observations; these values are the latest reported data, not live readings.")
fields = month.reset_index()
table = pd.DataFrame([{
    "Field": METRICS.get(column, column.replace("_", " ").title()),
    "Role": "Measure" if column in METRICS else "Metadata",
    "Latest value": "Not provided" if pd.isna(fields[column].iloc[-1]) else str(fields[column].iloc[-1]),
    "Latest month": fields[column].tolist() if pd.api.types.is_numeric_dtype(fields[column]) else [],
} for column in fields.columns])
st.dataframe(table, column_config={
    "Latest month": st.column_config.LineChartColumn("Latest month")}, hide_index=True, width="stretch")
st.caption("Each numeric field has its own sparkline scale. Dates and text use values; identifiers are metadata.")
st.caption("Sparklines follow observation order; horizontal spacing does not represent elapsed time.")
st.subheader("Latest reported observations")
st.dataframe(month.sort_index(ascending=False), width="stretch")
