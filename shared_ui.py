"""Shared dates and simple messages for the new pages."""
from contextlib import contextmanager
import pandas as pd
import streamlit as st
from pymongo.errors import PyMongoError
from atlas_data import AtlasSetupError, DatasetNotReady


def remember_dates():
    st.session_state['selected_period'] = st.session_state['_shared_period']


def choose_period(series, panel=None, compact=False):
    from popup_ui import controls_panel, in_popup
    panel = controls_panel() if panel is None else panel
    compact = compact or in_popup()
    first, last = series.index.min().date(), series.index.max().date()
    default = (max(first, pd.Timestamp('2024-01-01').date()), min(last, pd.Timestamp('2024-12-31').date()))
    if default[0] > default[1]:
        default = (first, last)
    saved = st.session_state.get('selected_period', default)
    if len(saved) != 2:
        saved = default
    saved = (max(first, min(saved[0], last)), max(first, min(saved[1], last)))
    if compact:
        # Separate fields keep each date readable in a narrow control panel.
        for key, value in zip(['_picker_start', '_picker_end'], saved):
            if key not in st.session_state or not first <= st.session_state[key] <= last:
                st.session_state[key] = value
        start = panel.date_input('Start date', min_value=first, max_value=last, key='_picker_start', format='YYYY-MM-DD')
        end = panel.date_input('End date', min_value=first, max_value=last, key='_picker_end', format='YYYY-MM-DD')
        if start > end:
            st.info('Start date must be before end date.')
            st.stop()
        st.session_state['selected_period'] = (start, end)
        return start, end
    st.session_state['_shared_period'] = saved
    dates = panel.date_input('Shared time frame', min_value=first, max_value=last,
                                 key='_shared_period', on_change=remember_dates)
    if len(dates) != 2 or dates[0] > dates[1]:
        st.info('Choose a start and an end date.')
        st.stop()
    st.session_state['selected_period'] = dates
    return dates


def area_id(series):
    kind, number = series.area_type.iloc[0], int(series.area_number.iloc[0])
    return f'NO{number}' if kind in ('NO', 'EL') else f'VASS{number}'


@contextmanager
def explain_errors():
    try:
        yield
    except (AtlasSetupError, DatasetNotReady) as error:
        st.info(str(error))
        st.stop()
    except PyMongoError:
        st.error('Atlas could not be reached. Check your private MONGO_URI and Atlas Network Access.')
        st.stop()
    except (ValueError, KeyError, TypeError, FileNotFoundError) as error:
        st.warning(str(error))
        st.stop()
