import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Area Analytics", page_icon="🗺️", layout="wide")

# Get theme background colors for transparent blending
bg_color = st.get_option("theme.backgroundColor") or "#0e1117"
card_bg = st.get_option("theme.secondaryBackgroundColor") or "#262730"
text_color = st.get_option("theme.textColor") or "#fafafa"

# Apply high-end UX theme defaults
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
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.alpha": 0.15,
        "grid.color": text_color,
        "grid.linestyle": "--",
    }
)

st.title("🗺️ Price Area Deep Dive")
st.markdown("Filter and inspect reservoir storage levels across Norway's bidding zones.")

try:
    df = load_data()

    # Identify primary date column
    primary_date = "date_id" if "date_id" in df.columns else df.columns[0]
    if not pd.api.types.is_datetime64_any_dtype(df[primary_date]):
        df[primary_date] = pd.to_datetime(df[primary_date].astype(str), errors="coerce")

    # Region Selector
    area_col = [c for c in df.columns if "area" in c.lower() or "price" in c.lower() or "el" in c.lower()]
    area_field = area_col[0] if area_col else None

    if area_field:
        areas = df[area_field].dropna().unique().tolist()
        selected_area = st.selectbox("Select Price Area / Bidding Zone", options=areas)
        df_filtered = df[df[area_field] == selected_area].sort_values(primary_date)
    else:
        df_filtered = df.sort_values(primary_date)

    st.subheader(f"Area Fill Dynamics: {selected_area if area_field else 'All Regions'}")

    fig, ax = plt.subplots(figsize=(12, 4.5), dpi=150)
    
    ax.plot(
        df_filtered[primary_date],
        df_filtered["fill_ratio"],
        color="#0F62FE",
        linewidth=2,
        label="Fill Ratio",
    )
    ax.fill_between(
        df_filtered[primary_date],
        df_filtered["fill_ratio"],
        color="#0F62FE",
        alpha=0.12,
    )

    ax.set_ylabel("Fill Ratio (0–1)", fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(text_color)
    ax.spines["bottom"].set_color(text_color)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

    legend = ax.legend(loc="upper left", frameon=True, fontsize=8.5)
    legend.get_frame().set_facecolor(card_bg)
    legend.get_frame().set_edgecolor("none")
    for text in legend.get_texts():
        text.set_color(text_color)

    plt.tight_layout()
    st.pyplot(fig)

except Exception as e:
    st.error(f"Error loading Area Analytics: {e}")
