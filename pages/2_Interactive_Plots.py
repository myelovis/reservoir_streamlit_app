import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Interactive Visualizations", page_icon="📈", layout="wide")

st.title("📈 Interactive Reservoir Data Plots")

try:
    df = load_data()
    sns.set_theme(style="whitegrid")

    # Extract distinct monthly periods for the select_slider
    df['year_month'] = df['date_id'].dt.to_period('M').astype(str)
    available_months = sorted(df['year_month'].unique().tolist())

    col1, col2 = st.columns([1, 2])

    with col1:
        # Dropdown for selecting columns or 'All Columns'
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        column_options = ["All Columns Together"] + numeric_cols
        selected_option = st.selectbox("Select Feature / Display Mode", options=column_options)

    with col2:
        # Selection slider to pick a range of months (default: first month)
        if len(available_months) > 1:
            default_selection = (available_months[0], available_months[0])
            selected_months = st.select_slider(
                "Select Month Range",
                options=available_months,
                value=default_selection
            )
        else:
            selected_months = (available_months[0], available_months[0])

    # Filter dataset according to slider selection
    start_m, end_m = selected_months
    filtered_df = df[(df['year_month'] >= start_m) & (df['year_month'] <= end_m)]

    st.markdown(f"**Showing data from {start_m} to {end_m}** ({len(filtered_df)} records)")

    # Plotting Section
    fig, ax = plt.subplots(figsize=(10, 4.5))

    if selected_option == "All Columns Together":
        # Normalize numeric columns to 0-1 scale to display together accurately
        norm_df = filtered_df[numeric_cols].apply(lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9))
        for col in numeric_cols:
            ax.plot(filtered_df['date_id'], norm_df[col], label=col, alpha=0.7)
        ax.set_title(f"Normalized Trends for All Metrics ({start_m} to {end_m})", fontsize=12, fontweight='bold')
        ax.set_ylabel("Normalized Value (0 - 1)")
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    else:
        ax.plot(filtered_df['date_id'], filtered_df[selected_option], color="#0066cc", linewidth=1.8)
        ax.set_title(f"Trend of '{selected_option}' ({start_m} to {end_m})", fontsize=12, fontweight='bold')
        ax.set_ylabel(selected_option)

    ax.set_xlabel("Date")
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)

except Exception as e:
    st.error(f"Error rendering plot: {e}")