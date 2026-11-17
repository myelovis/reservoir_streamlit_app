from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from reservoir_data import choose_area
from analysis import stl_analysis, spectrogram_analysis

@st.cache_data(ttl=3600, max_entries=12, show_spinner=False)
def pattern_plot(method, filling, first, second, robust, label):
    if method == 'STL':
        fig, table = stl_analysis(filling, first, second, robust, label)
    else:
        fig, table = spectrogram_analysis(filling, first, second, label)
    image = BytesIO()
    try:
        fig.savefig(image, format='png', dpi=110)
    finally:
        plt.close(fig)
    return image.getvalue(), table


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
    with st.form('stl_settings'):
        left, middle, right = st.columns(3)
        seasonal = left.number_input("Seasonal smoother (odd)", min_value=7, max_value=101, value=13, step=2)
        trend = middle.number_input("Trend smoother (weeks, odd)", min_value=53, max_value=521, value=89, step=2)
        robust = right.checkbox("Robust fitting", value=True)
        run_stl = st.form_submit_button('Run STL')
    context = (label, tuple(selected), int(seasonal), int(trend), robust)
    if run_stl:
        try:
            with st.spinner('Finding trend and seasonality…'):
                st.session_state['stl_plot'] = (context, pattern_plot('STL', filling, int(seasonal), int(trend), robust, label))
        except ValueError as error:
            st.warning(str(error))
    saved = st.session_state.get('stl_plot')
    if saved is None or saved[0] != context:
        st.info('Choose settings and click Run STL. Use at least two years.')
    else:
        image, components = saved[1]
        st.image(image)
        st.dataframe(components, width='stretch')
        st.download_button('Download STL components', components.to_csv().encode(), f'{label}_stl.csv', 'text/csv')

with spectral_tab:
    with st.form('spectrogram_settings'):
        left, right = st.columns(2)
        window = int(left.number_input('Window length (weeks)', 4, 520, 104))
        overlap = int(right.number_input('Window overlap (weeks)', 0, 519, 78))
        run_spectrum = st.form_submit_button('Run spectrogram')
    context = (label, tuple(selected), window, overlap)
    if run_spectrum:
        try:
            with st.spinner('Finding periodic patterns…'):
                st.session_state['spectrum_plot'] = (context, pattern_plot('Spectrum', filling, window, overlap, False, label))
        except ValueError as error:
            st.warning(str(error))
    saved = st.session_state.get('spectrum_plot')
    if saved is None or saved[0] != context:
        st.info('Choose settings and click Run spectrogram.')
    else:
        image, spectrum = saved[1]
        st.image(image)
        st.download_button('Download spectral power', spectrum.to_csv().encode(), f'{label}_spectrogram.csv', 'text/csv')
