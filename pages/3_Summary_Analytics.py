import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Summary Analytics", page_icon="📈", layout="wide")

st.title("📈 Summary Analytics & Trends")

try:
    # 1. Load dataset
    df = load_data()

    # 2. National level aggregation across date_id
    df_national = (
        df.groupby("date_id")
        .agg(
            {
                "capacity_twh": "sum",
                "storage_twh": "sum",
                "fill_ratio": "mean",
                "fill_ratio_previous_week": "mean",
                "fill_ratio_change": "mean",
            }
        )
        .reset_index()
    )

    # -------------------------------------------------------------
    # SECTION 1: Subplots Grid (One separate plot per feature)
    # -------------------------------------------------------------
    st.subheader("📊 Individual Feature Subplots")

    numeric_cols = [
        "capacity_twh",
        "storage_twh",
        "fill_ratio",
        "fill_ratio_previous_week",
        "fill_ratio_change",
    ]
    # Keep only columns present in the dataset
    numeric_cols = [c for c in numeric_cols if c in df_national.columns]

    n_cols = len(numeric_cols)
    fig_subplots, axes = plt.subplots(
        nrows=n_cols, ncols=1, figsize=(12, 3 * n_cols), sharex=True
    )

    if n_cols == 1:
        axes = [axes]

    for ax, col in zip(axes, numeric_cols):
        ax.plot(df_national["date_id"], df_national[col], color="#2b5c8f", linewidth=1.5)
        ax.set_title(col.replace("_", " ").title(), fontsize=11, fontweight="bold")
        ax.set_ylabel("Value", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.6)

    axes[-1].set_xlabel("Date", fontsize=10, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig_subplots)

    # -------------------------------------------------------------
    # SECTION 2: Combined Dual-Axis Plot (All Key Metrics Together)
    # -------------------------------------------------------------
    st.subheader("📈 Combined Metrics Plot (Dual Y-Axis)")

    fig_dual, ax1 = plt.subplots(figsize=(12, 5))

    color_cap = "#2b5c8f"
    color_stor = "#4682b4"
    color_ratio = "#d95f02"

    # Left Axis: TWh values
    ax1.set_xlabel("Date", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Energy Potential (TWh)", color=color_cap, fontsize=10, fontweight="bold")
    l1 = ax1.plot(
        df_national["date_id"],
        df_national["capacity_twh"],
        color=color_cap,
        linestyle="--",
        label="Capacity (TWh)",
    )
    l2 = ax1.plot(
        df_national["date_id"],
        df_national["storage_twh"],
        color=color_stor,
        linewidth=2,
        label="Storage (TWh)",
    )
    ax1.tick_params(axis="y", labelcolor=color_cap)

    # Right Axis: Fill Ratio Ratio
    ax2 = ax1.twinx()
    ax2.set_ylabel("Fill Ratio (0–1)", color=color_ratio, fontsize=10, fontweight="bold")
    l3 = ax2.plot(
        df_national["date_id"],
        df_national["fill_ratio"],
        color=color_ratio,
        linewidth=1.5,
        alpha=0.8,
        label="Mean Fill Ratio",
    )
    ax2.tick_params(axis="y", labelcolor=color_ratio)
    ax2.set_ylim(0, 1.05)

    # Merge legends
    lines = l1 + l2 + l3
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="upper left")
    ax1.grid(True, linestyle=":", alpha=0.5)

    st.pyplot(fig_dual)

except Exception as e:
    st.error(f"Error running summary analytics: {e}")
