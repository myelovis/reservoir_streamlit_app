import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from reservoir_data import choose_area
from analysis import stl_analysis, spectrogram_analysis

st.title("Reservoir Patterns")
st.write("Separate long-term movement from annual seasonality, then inspect how periodic patterns change over time.")
series = choose_area(default_kind="EL", default_number=3)
kind, number = series.area_type.iloc[0], int(series.area_number.iloc[0])
label = f"NO{number}" if kind == "EL" else ("Norway" if kind == "NO" else f"Watercourse {number}")
if len(series) < 104:
    st.info("Select an area with at least two years of weekly filling observations.")
    st.stop()
first, last = series.index.min().date(), series.index.max().date()
default_start = max(first, (pd.Timestamp(last) - pd.DateOffset(years=5)).date())
selected = st.date_input("Reservoir analysis period", (default_start, last), min_value=first,
                         max_value=last, key="reservoir_pattern_dates")
if len(selected) != 2:
    st.info("Choose a start and an end date.")
    st.stop()
filling = series.loc[str(selected[0]):str(selected[1]), "fill_ratio"] * 100
columns = st.columns(3)
columns[0].metric("Region", label)
columns[1].metric("Weekly observations", f"{len(filling):,}")
columns[2].metric("Average filling", f"{filling.mean():.1f}%" if len(filling) else "—")
st.caption("Source: MongoDB Atlas (NVE observations) · weekly filling (%) · no interpolation of missing weeks. The area selection is shared with the reservoir table and plots.")

stl_tab, spectral_tab = st.tabs(["STL decomposition", "Spectrogram"])
with stl_tab:
    st.subheader("Trend, seasonality and residuals")
    left, middle, right = st.columns(3)
    seasonal = left.number_input("Seasonal smoother (odd)", min_value=7, max_value=101, value=13, step=2)
    trend = middle.number_input("Trend smoother (weeks, odd)", min_value=53, max_value=521, value=89, step=2)
    robust = right.checkbox("Robust fitting", value=True)
    try:
        fig, components = stl_analysis(filling, int(seasonal), int(trend), robust, label)
    except ValueError as error:
        st.warning(str(error))
    else:
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Annual period ≈ 52 weeks. Larger smoothers produce smoother components. Robust fitting reduces the influence of unusual observations. pp = percentage points.")
        with st.expander("Decomposition values"):
            st.dataframe(components, width="stretch")
        st.download_button("Download STL components", components.to_csv().encode(), f"{label}_stl.csv", "text/csv")

with spectral_tab:
    st.subheader("Patterns through time")
    left, right = st.columns(2)
    window = int(left.number_input("Window length (weeks)", min_value=4, max_value=520, value=104, step=1))
    overlap = int(right.number_input("Window overlap (weeks)", min_value=0, max_value=519, value=78, step=1))
    try:
        fig, spectrum = spectrogram_analysis(filling, window, overlap, label)
    except ValueError as error:
        st.warning(str(error))
    else:
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Brighter bands indicate stronger periodic variation. The dashed line is the annual cycle. Longer windows improve frequency resolution but reduce time resolution; overlapping windows are not independent.")
        st.download_button("Download spectral power", spectrum.to_csv().encode(), f"{label}_spectrogram.csv", "text/csv")
