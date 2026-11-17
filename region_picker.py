"""Show the shared area, dates and map in a popup."""
import streamlit as st


@st.dialog('Select region and dates', width='large')
def open_region_picker():
    from streamlit_folium import st_folium
    from reservoir_data import choose_area
    from shared_ui import choose_period, area_id, explain_errors
    from map_tools import boundaries, colour_map
    from region_tools import clicked_area
    from weather_stats import PROPERTIES

    # Put controls inside this window, not in the sidebar.
    series = choose_area(default_kind='EL', default_number=3, panel=st)
    start, end = choose_period(series, panel=st)
    kind = str(series.area_type.iloc[0])
    mode = st.selectbox('Colour by', ['Price area', 'Water area', 'Weather property'])
    prop = st.selectbox('Weather property', list(PROPERTIES)[:2],
                       format_func=lambda value: PROPERTIES[value][0], disabled=mode != 'Weather property')
    with explain_errors():
        areas = boundaries(kind)
        colour_kind = {'Price area': 'EL', 'Water area': 'VASS', 'Weather property': 'Weather'}[mode]
        figure, missing = colour_map(areas, colour_kind, prop, start, end, area_id(series))
        event = st_folium(figure, height=420, use_container_width=True, key=f'picker_map_{kind}',
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
        st.caption(f'Selected: {area_id(series)} · {start} to {end}')
        if missing:
            st.info('No prepared weather: ' + ', '.join(missing))
    if st.button('Done', type='primary'):
        st.rerun()  # Close the window; the shared choices are already saved.
