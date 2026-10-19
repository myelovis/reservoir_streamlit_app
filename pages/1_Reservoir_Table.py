import streamlit as st
import pandas as pd
from reservoir_data import choose_area, METRICS

st.set_page_config(page_title="Megasinstatistikk Data Overview", layout="wide")
st.title("Megasinstatistikk Data Overview")

# Load area series data
series = choose_area().sort_index()

if series.empty:
    st.info("No data available for the selected area.")
    st.stop()

# Get the first (earliest) date and first month from the series
first_date = series.index.min()
first_month_period = first_date.to_period("M")

# Filter series to get records from the first month
first_month = series.loc[series.index.to_period("M") == first_month_period]

st.caption(f"First available observation: {first_date:%d %B %Y}. Sparklines show {first_month_period}.")
st.caption("NVE publishes weekly observations; sparklines below display data from the first recorded month.")

fields = first_month.reset_index()

# Build table rows cleanly
table_data = []

for column in fields.columns:
    is_measure = column in METRICS
    role = "Measure" if is_measure else "Metadata"
    
    # Get the latest value from the first month subset
    last_val = fields[column].iloc[-1] if not fields[column].empty else None
    latest_val_str = "Not provided" if pd.isna(last_val) else str(last_val)
    
    # Generate sparkline array ONLY for numeric measures (excludes Area Number, Iso Year, Iso Week, etc.)
    if is_measure and pd.api.types.is_numeric_dtype(fields[column]):
        sparkline_data = fields[column].dropna().tolist()
    else:
        sparkline_data = []

    table_data.append({
        "Field": METRICS.get(column, column.replace("_", " ").title()),
        "Role": role,
        "Value (First Month)": latest_val_str,
        "First month": sparkline_data
    })

table = pd.DataFrame(table_data)

# Display table with LineChartColumn on row-wise lists
st.dataframe(
    table,
    column_config={
        "First month": st.column_config.LineChartColumn(
            "First month", 
            width="medium"
        )
    },
    hide_index=True,
    use_container_width=True
)

st.caption("Each numeric measure field displays its line chart for the first recorded month.")

st.subheader("First month reported observations")
st.dataframe(first_month.sort_index(ascending=True), use_container_width=True)
