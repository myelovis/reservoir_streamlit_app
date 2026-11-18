"""Open an existing analysis in a laptop-sized window."""
from pathlib import Path
import runpy
import streamlit as st
from popup_ui import popup_layout

ROOT = Path(__file__).resolve().parent
PAGES = {
    'Reservoir table': '1_Reservoir_Table.py',
    'Reservoir plots': '2_Reservoir_Plots.py',
    'Electricity transfers': '5_Electricity_Transfers.py',
    'STL and spectrogram': '3_Reservoir_Patterns.py',
    'Weather outliers': '4_Weather_Outliers.py',
    'ACF and PACF': '8_Autocorrelation.py',
    'Sliding window correlation': '6_Weather_Correlation.py',
    'Reservoir forecast': '7_Filling_Forecast.py',
}


def close_analysis():
    st.session_state.pop('analysis_popup_label', None)


def open_analysis(label):
    @st.dialog(label, width='large', on_dismiss=close_analysis)
    def show():
        with st.container(key='analysis_popup'):
            panel = st.container()
            if label != 'Electricity transfers':
                with st.popover('Region and dates'):
                    panel = st.container()
            with popup_layout(panel):
                # Only run a known local page. Its calculations stay unchanged.
                runpy.run_path(str(ROOT/'pages'/PAGES[label]), run_name='__main__')
    show()
