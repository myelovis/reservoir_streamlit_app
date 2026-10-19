import streamlit as st
import pandas as pd
from reservoir_data import choose_area, METRICS

st.set_page_config(page_title="Reservoir Data Overview", page_icon="📊", layout="wide")

st.title("📊 Reservoir Data Overview")
st.markdown(
    "Row-wise tabular view displaying summary statistics per feature, "
    "with embedded sparkline charts showing data trends for the first month."
)

try:
    # Load area-filtered dataframe
    df = choose_area().sort_index()

    if df.empty:
        st.info("No data available for the selected area.")
        st.stop()

    # Reset index if date_id is currently the DataFrame index
    df_reset = df.reset_index()
    date_col = "date_id" if "date_id" in df_reset.columns else df_reset.columns[0]
    
    # Ensure date column is datetime
    df_reset[date_col] = pd.to_datetime(df_reset[date_col])

    # Filter data for the first month (first 30 days of the dataset)
    start_date = df_reset[date_col].min()
    end_date = start_date + pd.Timedelta(days=30)
    first_month_df = df_reset[(df_reset[date_col] >= start_date) & (df_reset[date_col] <= end_date)]

    # Identify numeric columns
    numeric_cols = df_reset.select_dtypes(include=["float64", "int64", "float32", "int32"]).columns.tolist()

    # Build row-wise summary metrics list
    overview_list = []
    
    for col in numeric_cols:
        # Exclude metadata identifiers (year, week, area_id) from sparkline rendering if needed
        is_measure = col in METRICS or col not in ["iso_year", "iso_week", "area_as_integer"]
        
        # Extract first month trend array chronologically for real measures
        if is_measure:
            series_first_month = first_month_df[col].dropna().tolist()
        else:
            series_first_month = []

        feature_label = METRICS.get(col, col.replace("_", " ").title())

        overview_list.append({
            "Metric / Feature": feature_label,
            "Role": "Measure" if is_measure else "Metadata",
            "Total Samples": int(df_reset[col].count()),
            "Mean Value": float(df_reset[col].mean()) if is_measure else None,
            "Min Value": float(df_reset[col].min()) if is_measure else None,
            "Max Value": float(df_reset[col].max()) if is_measure else None,
            "First Month Trend": series_first_month
        })

    overview_df = pd.DataFrame(overview_list)

    # Render interactive table with embedded LineChartColumn
    st.dataframe(
        overview_df,
        column_config={
            "Metric / Feature": st.column_config.TextColumn("Feature Name", help="Name or mapped title of the dataset field"),
            "Role": st.column_config.TextColumn("Role"),
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
    st.error(f"Error loading reservoir dataset: {e}")
