"""Shared dates and simple messages for the new pages."""
from contextlib import contextmanager
import pandas as pd
import streamlit as st
from pymongo.errors import PyMongoError
from atlas_data import AtlasSetupError, DatasetNotReady


def remember_dates():
    st.session_state['selected_period'] = st.session_state['_shared_period']


def period_bounds(series, weather_dates=False):
    """Home can include weather years before reservoir records begin."""
    first, last = series.index.min().date(), series.index.max().date()
    if weather_dates:
        from weather_data import weather_years
        years = weather_years(area_id(series))
        if years:
            first = min(first, pd.Timestamp(f'{years[0]}-01-01').date())
            last = max(last, pd.Timestamp(f'{years[-1]}-12-31').date())
    return first, last


def check_reservoir_period(series, dates):
    selected = series.loc[str(dates[0]):str(dates[1])]
    first, last = series.index.min().date(), series.index.max().date()
    if selected.empty:
        st.info(f'No reservoir observations in this period. {area_id(series)} reservoir data covers '
                f'{first} to {last}. Weather outliers can still use earlier published weather.')
        st.stop()
    if dates[0] < first or dates[1] > last:
        st.caption(f'Reservoir calculations use the available observations: '
                   f'{selected.index.min().date()} to {selected.index.max().date()}.')


def choose_period(series, panel=None, compact=False, weather_dates=False):
    from popup_ui import controls_panel, in_popup, uses_home_selection
    if uses_home_selection():
        dates = st.session_state.get('selected_period', ())
        if len(dates) != 2 or dates[0] > dates[1]:
            st.info('Choose a start and end date on Home.')
            st.stop()
        if not weather_dates:
            check_reservoir_period(series, dates)
        return tuple(dates)
    panel = controls_panel() if panel is None else panel
    compact = compact or in_popup()
    with explain_errors():
        first, last = period_bounds(series, weather_dates)
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

