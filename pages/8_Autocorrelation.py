"""Check how weekly filling relates to its past values."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.stattools import acf, pacf
from analysis import regular_series
from reservoir_data import choose_area
from shared_ui import choose_period, area_id, explain_errors


@st.cache_data(ttl=3600, max_entries=16, show_spinner=False)
def correlations(values, lags, difference):
    y = regular_series(values, '7D', minimum=12)
    if difference:
        y = y.diff().dropna()
    if lags >= len(y) // 2:
        raise ValueError('Choose fewer lags or a longer time frame.')
    if y.std() <= np.finfo(float).eps:
        raise ValueError('The selected series is constant. Choose another time frame.')
    a, a_limits = acf(y, nlags=lags, alpha=.05, fft=True)
    p, p_limits = pacf(y, nlags=lags, alpha=.05, method='ywm')
    return [(a, a_limits), (p, p_limits)]


st.title('ACF and PACF')
series = choose_area(default_kind='EL', default_number=3)
start, end = choose_period(series)
with st.form('autocorrelation_settings'):
    lags = st.slider('Lags (weeks)', 1, 52, 12)
    difference = st.checkbox('Use weekly changes', value=True)
    run = st.form_submit_button('Run ACF / PACF')

context = (area_id(series), start, end, lags, difference)
with explain_errors():
    if run:
        values = series.loc[str(start):str(end), 'fill_ratio'] * 100
        with st.spinner('Checking weekly relationships…'):
            st.session_state['correlation_plots'] = (context, correlations(values, lags, difference))
    saved = st.session_state.get('correlation_plots')
    if saved is None or saved[0] != context:
        st.info('Choose settings and click Run ACF / PACF.')
        st.stop()
    for tab, (values, limits), name in zip(st.tabs(['ACF', 'PACF']), saved[1], ['ACF', 'PACF']):
        with tab:
            # Skip lag zero: each value is perfectly related to itself.
            x = np.arange(1, len(values))
            fig = go.Figure()
            fig.add_scatter(x=x, y=limits[1:, 0] - values[1:], mode='lines', line_width=0, showlegend=False)
            fig.add_scatter(x=x, y=limits[1:, 1] - values[1:], mode='lines', line_width=0,
                            fill='tonexty', fillcolor='rgba(36,122,145,0.15)', name='Approx. 95% band')
            fig.add_bar(x=x, y=values[1:], marker_color='#247a91', name=name)
            fig.update_layout(title=f'{area_id(series)} · {name}', xaxis_title='Lag (weeks)',
                              yaxis_title='Correlation', template='plotly_white', height=380)
            st.plotly_chart(fig, width='stretch')
    st.caption('ACF includes indirect relationships; PACF adjusts for shorter lags. These bands are approximate. Correlation does not establish causation or select a model by itself.')
