import pandas as pd
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Data Overview", page_icon="📊", layout="wide")

st.title("📊 Reservoir Data Overview")
st.markdown(
    "Row-wise tabular view displaying one row per feature column, "
    "with embedded sparkline charts showing data trends for the first month."
)

try:
    df = load_data()

    # Filter data for the first month (30 days) of the series
    start_date = df['date_id'].min()
    end_date = start_date + pd.Timedelta(days=30)
    first_month_df = df[(df['date_id'] >= start_date) & (df['date_id'] <= end_date)]

    # Filter numeric columns for sparkline rendering
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()

    overview_list = []
    for col in numeric_cols:
        series_first_month = first_month_df[col].dropna().tolist()
        overview_list.append({
            "Metric / Feature": col,
            "Total Samples": int(df[col].count()),
            "Mean Value": float(df[col].mean()),
            "Min Value": float(df[col].min()),
            "Max Value": float(df[col].max()),
            "First Month Trend": series_first_month
        })

    overview_df = pd.DataFrame(overview_list)

    # Render interactive table with embedded LineChartColumn
    st.dataframe(
        overview_df,
        column_config={
            "Metric / Feature": st.column_config.TextColumn("Feature Name", help="Name of the CSV column"),
            "Total Samples": st.column_config.NumberColumn("Count"),
            "Mean Value": st.column_config.NumberColumn("Mean", format="%.4f"),
            "Min Value": st.column_config.NumberColumn("Min", format="%.4f"),
            "Max Value": st.column_config.NumberColumn("Max", format="%.4f"),
            "First Month Trend": st.column_config.LineChartColumn(
                "First Month Trend (Line Chart)",
                help="Inline trend visualization over the first 30 days of records.",
                width="medium"
            ),
        },
        hide_index=True,
        use_container_width=True
    )

except Exception as e:
    st.error(f"Error loading dataset: {e}")