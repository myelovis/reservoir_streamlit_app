"""Show the shared area, dates and map in a popup."""
import streamlit as st


@st.dialog('Select region and dates', width='large')
def open_region_picker():
    from streamlit_folium import st_folium
    from reservoir_data import choose_area
    from shared_ui import choose_period, area_id, explain_errors
    from map_tools import boundaries, colour_map
    from region_tools import clicked_area
    from weather_data import weather_years
    from weather_stats import PROPERTIES

    with st.container(key='region_picker'):
        controls, map_panel = st.columns([.15, .85], gap='small')
        with controls:
            series = choose_area(default_kind='EL', default_number=3, panel=st, compact=True)
            start, end = choose_period(series, panel=st, compact=True, weather_dates=True)
            kind = str(series.area_type.iloc[0])
            mode = st.selectbox('Colour by', ['Price area', 'Water area', 'Weather property'])
            prop = 'temperature_2m'
            if mode == 'Weather property':
                prop = st.selectbox('Weather property', list(PROPERTIES)[:2],
                                   format_func=lambda value: PROPERTIES[value][0])
            if st.button('Done', type='primary', width='stretch'):
                st.rerun()  # Close the popup; shared choices stay saved.
        with map_panel, explain_errors():
            region = area_id(series)
            reservoir_first = series.index.min().date()
            reservoir_last = series.index.max().date()
            years = weather_years(region)
            st.caption(f'{region} reservoir observations · {reservoir_first} to {reservoir_last}')
            if years:
                st.caption('Complete ERA5 years · ' + ', '.join(map(str, years)))
            else:
                st.caption(f'No complete ERA5 years are published for {region} in the connected Atlas database.')
            areas = boundaries(kind)
            colour_kind = {'Price area': 'EL', 'Water area': 'VASS', 'Weather property': 'Weather'}[mode]
            figure, missing = colour_map(areas, colour_kind, prop, start, end, area_id(series))
            event = st_folium(figure, height=400, use_container_width=True, key=f'picker_map_{kind}',
                             returned_objects=['last_clicked', 'last_object_clicked'])
            click = event.get('last_clicked') or event.get('last_object_clicked')
            if click:
                token = (kind, click['lat'], click['lng'])
                if st.session_state.get('picker_click') != token:
                    st.session_state['picker_click'] = token
                    chosen = clicked_area(areas, click['lat'], click['lng'])
                    if chosen is not None:
                        st.session_state['selected_area_type'] = chosen.area_type
                        st.session_state['selected_area_number'] = int(chosen.area_number)
                        st.rerun(scope='fragment')
            st.caption(f'{area_id(series)} · {start} to {end} · Click an area to select it.')
            if missing:
                st.info('No prepared weather: ' + ', '.join(missing))
