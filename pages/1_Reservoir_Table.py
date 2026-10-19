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

latest_date = series.index.max()
latest_month = latest_date.to_period("M")

# Filter series for the latest month
month = series.loc[series.index.to_period("M") == latest_month]

st.caption(f"Latest available observation: {latest_date:%d %B %Y}. Sparklines show {latest_month}.")
st.caption("NVE publishes weekly observations; these values are the latest reported data, not live readings.")

fields = month.reset_index()

# Build table rows cleanly
table_data = []

for column in fields.columns:
    is_measure = column in METRICS
    role = "Measure" if is_measure else "Metadata"
    
    # Get the latest reported value formatted nicely
    last_val = fields[column].iloc[-1] if not fields[column].empty else None
    latest_val_str = "Not provided" if pd.isna(last_val) else str(last_val)
    
    # CRITICAL FIX: Only generate sparkline values for actual numeric measures.
    # Metadata like 'Area Number', 'Iso Year', 'Iso Week' should NOT have sparklines.
    if is_measure and pd.api.types.is_numeric_dtype(fields[column]):
        # Extract numeric series ordered chronologically
        sparkline_data = fields[column].dropna().tolist()
    else:
        sparkline_data = []

    table_data.append({
        "Field": METRICS.get(column, column.replace("_", " ").title()),
        "Role": role,
        "Latest value": latest_val_str,
        "Latest month": sparkline_data
    })

table = pd.DataFrame(table_data)

st.dataframe(
    table,
    column_config={
        "Latest month": st.column_config.LineChartColumn(
            "Latest month", 
            width="medium"
        )
    },
    hide_index=True,
    use_container_width=True
)

st.caption("Each numeric field has its own sparkline scale. Dates and text use values; identifiers are metadata.")
st.caption("Sparklines follow observation order; horizontal spacing does not represent elapsed time.")

st.subheader("Latest reported observations")
st.dataframe(month.sort_index(ascending=False), use_container_width=True)
