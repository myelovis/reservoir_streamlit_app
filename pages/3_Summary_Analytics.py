import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Summary Analytics", page_icon="📈", layout="wide")

# Streamlit Dynamic UI Theme Extraction
bg_color = st.get_option("theme.backgroundColor") or "#0e1117"
card_bg = st.get_option("theme.secondaryBackgroundColor") or "#262730"
text_color = st.get_option("theme.textColor") or "#fafafa"

# Set global executive-level design defaults
plt.rcParams.update(
    {
        "figure.facecolor": bg_color,
        "axes.facecolor": bg_color,
        "savefig.facecolor": bg_color,
        "text.color": text_color,
        "axes.labelcolor": text_color,
        "xtick.color": text_color,
        "ytick.color": text_color,
        "font.family": "sans-serif",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.grid": True,
        "grid.alpha": 0.15,
        "grid.color": text_color,
        "grid.linestyle": "--",
        "figure.autolayout": False,
    }
)

st.title("📈 Hydropower Summary Analytics")
st.markdown(
    "Publication-quality overview of national hydropower metrics and combined fill ratio dynamics."
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

        # Clean Area Fill for Delta/Change Metrics
        if "change" in col or "delta" in col:
            ax.plot(x_axis, df_proc[col], color="#8d8d8d", linewidth=0.8)
            ax.fill_between(
                x_axis,
                df_proc[col],
                0,
                where=(df_proc[col] >= 0),
                color="#24a148",
                alpha=0.4,
                label="Inflow/Fill",
            )
            ax.fill_between(
                x_axis,
                df_proc[col],
                0,
                where=(df_proc[col] < 0),
                color="#da1e28",
                alpha=0.4,
                label="Outflow/Drain",
            )
            ax.axhline(0, color=text_color, linewidth=0.6, linestyle="--", alpha=0.5)

        # High-Contrast Accent Blue Line + Subtle Glow Shading
        else:
            ax.plot(
                x_axis,
                df_proc[col],
                color="#78a9ff",
                linewidth=1.5,
                label=title_str,
            )
            ax.fill_between(x_axis, df_proc[col], color="#78a9ff", alpha=0.1)

        # UI Refinement
        ax.set_title(col.replace("_", " ").upper(), loc="left", pad=6, color=text_color)
        ax.set_ylabel(title_str, fontsize=8.5, color=text_color)
        ax.tick_params(axis="both", which="major", labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(text_color)
        ax.spines["bottom"].set_color(text_color)

        legend = ax.legend(loc="upper left", frameon=True, fontsize=8)
        legend.get_frame().set_facecolor(card_bg)
        legend.get_frame().set_edgecolor("none")
        for text in legend.get_texts():
            text.set_color(text_color)

    # Smart X-Axis Date Formatting
    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    formatter = mdates.ConciseDateFormatter(locator)

    for ax in axes_flat[:num_plots]:
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

    # Clean up unused grid cells
    for unused_ax in axes_flat[num_plots:]:
        fig.delaxes(unused_ax)

    fig.subplots_adjust(hspace=0.28, wspace=0.18)
    return fig, axes


# Streamlit Execution Logic
try:
    df = load_data()

    primary_date = "date_id" if "date_id" in df.columns else df.columns[0]

    if not pd.api.types.is_datetime64_any_dtype(df[primary_date]):
        df[primary_date] = pd.to_datetime(df[primary_date].astype(str), errors="coerce")

    # -------------------------------------------------------------
    # SECTION 1: Subplots Grid
    # -------------------------------------------------------------
    st.subheader("📊 Individual Feature Subplots")
    fig_grid, axes_grid = plot_hydropower_analytics(df, date_col=primary_date)
    st.pyplot(fig_grid)

    # -------------------------------------------------------------
    # SECTION 2: Combined Dual-Axis Plot
    # -------------------------------------------------------------
    st.subheader("📈 Combined Metrics Plot (Dual Y-Axis)")

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

    color_cap = "#78a9ff"
    color_stor = "#33b1ff"
    color_ratio = "#ff8389"

    # Left Y-Axis: Capacity & Storage
    ax1.set_xlabel("Date", fontsize=9.5, fontweight="bold", color=text_color)
    ax1.set_ylabel(
        "Energy Potential (TWh)", color=color_cap, fontsize=9.5, fontweight="bold"
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
        "Fill Ratio (0–1)", color=color_ratio, fontsize=9.5, fontweight="bold"
    )
    l3 = ax2.plot(
        df_national[primary_date],
        df_national["fill_ratio"],
        color=color_ratio,
        linewidth=1.8,
        alpha=0.9,
        label="Mean Fill Ratio",
    )
    ax2.tick_params(axis="y", labelcolor=color_ratio)
    ax2.set_ylim(0, 1.05)
    ax2.set_facecolor("none")  # Ensure twin axis stays transparent

    # Border aesthetics
    for ax in [ax1, ax2]:
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_color(text_color)
        ax.spines["left"].set_color(text_color)
        ax.spines["right"].set_color(text_color)

    ax1.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax1.xaxis.get_major_locator()))

    # Single blended legend
    lines = l1 + l2 + l3
    labels = [line.get_label() for line in lines]
    legend_dual = ax1.legend(lines, labels, loc="upper left", frameon=True)
    legend_dual.get_frame().set_facecolor(card_bg)
    legend_dual.get_frame().set_edgecolor("none")
    for text in legend_dual.get_texts():
        text.set_color(text_color)

    plt.tight_layout()
    st.pyplot(fig_dual)

except Exception as e:
    st.error(f"Error rendering hydropower analytics: {e}")
