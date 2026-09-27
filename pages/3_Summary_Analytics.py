import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Summary Analytics", page_icon="📈", layout="wide")

st.title("📈 Summary Analytics & Combined Trends")

try:
    # 1. Load the dataset first
    df = load_data()

    # 2. Aggregate national totals/averages across price areas per date
    df_national = (
        df.groupby("date_id")
        .agg(
            {
                "capacity_twh": "sum",
                "storage_twh": "sum",
                "fill_ratio": "mean",
            }
        )
        .reset_index()
    )

    st.subheader("Dual Axis Plot: Energy Volume vs. Fill Ratio")

    # Dual Y-Axis Chart
    fig, ax1 = plt.subplots(figsize=(12, 5))

    color_cap = "#2b5c8f"
    color_stor = "#4682b4"
    color_ratio = "#d95f02"

    # Left Y-Axis: Energy Capacity & Storage (TWh)
    ax1.set_xlabel("Date", fontsize=10, fontweight="bold")
    ax1.set_ylabel(
        "Energy Potential (TWh)", color=color_cap, fontsize=10, fontweight="bold"
    )
    line1 = ax1.plot(
        df_national["date_id"],
        df_national["capacity_twh"],
        color=color_cap,
        linestyle="--",
        linewidth=1.5,
        label="Capacity (TWh)",
    )
    line2 = ax1.plot(
        df_national["date_id"],
        df_national["storage_twh"],
        color=color_stor,
        linewidth=2,
        label="Storage (TWh)",
    )
    ax1.tick_params(axis="y", labelcolor=color_cap)

    # Right Y-Axis: Fill Ratio
    ax2 = ax1.twinx()
    ax2.set_ylabel(
        "Fill Ratio (0–1)", color=color_ratio, fontsize=10, fontweight="bold"
    )
    line3 = ax2.plot(
        df_national["date_id"],
        df_national["fill_ratio"],
        color=color_ratio,
        linewidth=1.5,
        alpha=0.8,
        label="Mean Fill Ratio",
    )
    ax2.tick_params(axis="y", labelcolor=color_ratio)
    ax2.set_ylim(0, 1.05)

    # Combine legends
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left")
    ax1.grid(True, linestyle=":", alpha=0.5)

    st.pyplot(fig)

    st.subheader("Normalized Trend Comparison (0–1 Scale)")

    # Min-Max Normalized Visual Comparison
    df_normalized = df_national.copy()
    for col in ["capacity_twh", "storage_twh", "fill_ratio"]:
        min_v = df_normalized[col].min()
        max_v = df_normalized[col].max()
        df_normalized[col] = (df_normalized[col] - min_v) / (max_v - min_v)

    fig_norm, ax_norm = plt.subplots(figsize=(12, 4))
    ax_norm.plot(
        df_normalized["date_id"],
        df_normalized["capacity_twh"],
        label="Capacity (Normalized)",
        linestyle="--",
    )
    ax_norm.plot(
        df_normalized["date_id"],
        df_normalized["storage_twh"],
        label="Storage (Normalized)",
    )
    ax_norm.plot(
        df_normalized["date_id"],
        df_normalized["fill_ratio"],
        label="Fill Ratio (Normalized)",
        alpha=0.7,
    )

    ax_norm.set_xlabel("Date", fontsize=10)
    ax_norm.set_ylabel("Normalized Scale (0 to 1)", fontsize=10)
    ax_norm.legend(loc="upper left")
    ax_norm.grid(True, linestyle=":", alpha=0.5)

    st.pyplot(fig_norm)

except Exception as e:
    st.error(f"Error executing analytics: {e}")
