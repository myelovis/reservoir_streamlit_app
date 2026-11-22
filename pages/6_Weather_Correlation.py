from ui_feedback import show_chart
from popup_ui import in_popup, page_title, settings
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


page_title("Reservoir Patterns")
if not in_popup():
    st.write("Separate long-term movement from annual seasonality, then inspect how periodic patterns change over time.")
series = choose_area(default_kind="EL", default_number=3)
kind, number = series.area_type.iloc[0], int(series.area_number.iloc[0])
label = f"NO{number}" if kind == "EL" else ("Norway" if kind == "NO" else f"Watercourse {number}")
if len(series) < 104:
    st.info("Select an area with at least two years of weekly filling observations.")
    st.stop()
first, last = series.index.min().date(), series.index.max().date()
default_start = max(first, (pd.Timestamp(last) - pd.DateOffset(years=5)).date())
from popup_ui import uses_home_selection
if uses_home_selection():
    from shared_ui import choose_period
    selected = choose_period(series)
else:
    with settings('Analysis dates'):
        selected = st.date_input("Reservoir analysis period", (default_start, last), min_value=first,
                                 max_value=last, key="reservoir_pattern_dates")
if len(selected) != 2:
    st.info("Choose a start and an end date.")
    st.stop()
filling = series.loc[str(selected[0]):str(selected[1]), "fill_ratio"] * 100
st.caption(f'{label} · {len(filling)} weekly observations · filling (%) · NVE API')

stl_tab, spectral_tab = st.tabs(["STL decomposition", "Spectrogram"])
with stl_tab:
    if not in_popup():
        st.subheader("Trend, seasonality and residuals")
    with settings('STL settings'):
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
        if in_popup():
            from plotly.subplots import make_subplots
            import plotly.graph_objects as go
            figure = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=.06)
            for row, name in enumerate(components, start=1):
                figure.add_trace(go.Scatter(x=components.index,y=components[name],name=name,line_color='#205b3d'),row=row,col=1)
            figure.update_layout(height=290,margin=dict(t=15,b=20),showlegend=True)
            show_chart(figure)
        else:
            st.image(image)
        with st.expander('Decomposition values'):
            st.dataframe(components, height=220, width='stretch')
        st.download_button('Download STL components', components.to_csv().encode(), f'{label}_stl.csv', 'text/csv')

with spectral_tab:
    with settings('Spectrogram settings'):
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
        if in_popup():
            import numpy as np
            import plotly.graph_objects as go
            power = spectrum.to_numpy().T
            db = 10*np.log10(np.maximum(power/max(float(power.max()),np.finfo(float).tiny),1e-12))
            figure = go.Figure(go.Heatmap(x=spectrum.index,y=spectrum.columns,z=db,colorscale='Greens',zmin=-60,zmax=0))
            figure.update_layout(height=290,margin=dict(t=10,b=35),yaxis_title='Cycles / year',yaxis_range=[0,6])
            show_chart(figure)
        else:
            st.image(image)
        st.download_button('Download spectral power' , spectrum.to_csv().encode(), f'{label}_spectrogram.csv', 'text/csv')
