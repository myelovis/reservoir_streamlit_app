import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Summary Analytics", page_icon="📈", layout="wide")

st.title("📈 Hydropower Summary Analytics")
st.markdown(
    "Publication-quality overview of national hydropower metrics and combined fill ratio dynamics."
)

# Set global publication-quality defaults
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "semibold",
        "axes.labelsize": 9,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "figure.autolayout": False,
    }
)


def plot_hydropower_analytics(
    data: pd.DataFrame, date_col: str = "date_id", cols_per_row: int = 2
):
    df_proc = data.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_proc[date_col]):
        df_proc[date_col] = pd.to_datetime(
            df_proc[date_col].astype(str), errors="coerce"
        )

    df_proc = df_proc.sort_values(by=date_col).reset_index(drop=True)
    numeric_cols = df_proc.select_dtypes(include=["number"]).columns.drop(
        date_col, errors="ignore"
    )

    num_plots = len(numeric_cols)
    if num_plots == 0:
        raise ValueError("No numeric metrics detected for visualization.")

    n_rows = int(np.ceil(num_plots / cols_per_row))
    fig, axes = plt.subplots(
        nrows=n_rows,
        ncols=cols_per_row,
        figsize=(14, 3.2 * n_rows),
        sharex=True,
        dpi=150,
    )
    axes_flat = np.atleast_1d(axes).flatten()

    x_axis = df_proc[date_col]

    for idx, col in enumerate(numeric_cols):
        ax = axes_flat[idx]
        title_str = col.replace("_", " ").title()

        # Clean Area Fill for Delta/Change Metrics (Fixes the hairbrush visual error)
        if "change" in col or "delta" in col:
            ax.plot(x_axis, df_proc[col], color="#555555", linewidth=0.7)
            ax.fill_between(
                x_axis,
                df_proc[col],
                0,
                where=(df_proc[col] >= 0),
                color="#0E6027",
                alpha=0.5,
                label="Inflow/Fill",
            )
            ax.fill_between(
                x_axis,
                df_proc[col],
                0,
                where=(df_proc[col] < 0),
                color="#DA1E28",
                alpha=0.5,
                label="Outflow/Drain",
            )
            ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

        # High-Contrast Blue Line + Light Shading for Standard Metrics
        else:
            ax.plot(
                x_axis,
                df_proc[col],
                color="#0F62FE",
                linewidth=1.4,
                label=title_str,
            )
            ax.fill_between(x_axis, df_proc[col], color="#0F62FE", alpha=0.08)

        # Styling
        ax.set_title(col.replace("_", " ").upper(), loc="left", pad=6)
        ax.set_ylabel(title_str, fontsize=8.5)
        ax.tick_params(axis="both", which="major", labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=8)

    # Smart X-Axis Date Formatting
    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    formatter = mdates.ConciseDateFormatter(locator)

    for ax in axes_flat[:num_plots]:
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

    # Clean up empty subplots
    for unused_ax in axes_flat[num_plots:]:
        fig.delaxes(unused_ax)

    fig.subplots_adjust(hspace=0.25, wspace=0.18)
    return fig, axes


# Streamlit Execution Logic
try:
    df = load_data()

    # Determine date column name safely
    primary_date = "date_id" if "date_id" in df.columns else df.columns[0]

    # Ensure datetime format for aggregation and plotting
    if not pd.api.types.is_datetime64_any_dtype(df[primary_date]):
        df[primary_date] = pd.to_datetime(df[primary_date].astype(str), errors="coerce")

    # -------------------------------------------------------------
    # SECTION 1: Subplots Grid (One separate plot per feature)
    # -------------------------------------------------------------
    st.subheader("📊 Individual Feature Subplots")
    fig_grid, axes_grid = plot_hydropower_analytics(df, date_col=primary_date)
    st.pyplot(fig_grid)

    # -------------------------------------------------------------
    # SECTION 2: Combined Dual-Axis Plot (All Key Metrics Together)
    # -------------------------------------------------------------
    st.subheader("📈 Combined Metrics Plot (Dual Y-Axis)")

    # Group nationally by date for coherent trend comparison
    df_national = (
        df.groupby(primary_date)
        .agg(
            {
                "capacity_twh": "sum",
                "storage_twh": "sum",
                "fill_ratio": "mean",
            }
        )
        .reset_index()
    )

    fig_dual, ax1 = plt.subplots(figsize=(12, 5), dpi=150)

    color_cap = "#2b5c8f"
    color_stor = "#4682b4"
    color_ratio = "#d95f02"

    # Left Y-Axis: Energy Capacity & Storage (TWh)
    ax1.set_xlabel("Date", fontsize=10, fontweight="bold")
    ax1.set_ylabel(
        "Energy Potential (TWh)", color=color_cap, fontsize=10, fontweight="bold"
    )
    l1 = ax1.plot(
        df_national[primary_date],
        df_national["capacity_twh"],
        color=color_cap,
        linestyle="--",
        linewidth=1.5,
        label="Capacity (TWh)",
    )
    l2 = ax1.plot(
        df_national[primary_date],
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
    l3 = ax2.plot(
        df_national[primary_date],
        df_national["fill_ratio"],
        color=color_ratio,
        linewidth=1.5,
        alpha=0.8,
        label="Mean Fill Ratio",
    )
    ax2.tick_params(axis="y", labelcolor=color_ratio)
    ax2.set_ylim(0, 1.05)

    # Format X-Axis Dates cleanly
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax1.xaxis.get_major_locator()))

    # Merge legends from both axes
    lines = l1 + l2 + l3
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="upper left", frameon=True, framealpha=0.9)

    plt.tight_layout()
    st.pyplot(fig_dual)

except Exception as e:
    st.error(f"Error rendering hydropower analytics: {e}")
