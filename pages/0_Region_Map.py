import streamlit as st
from streamlit_folium import st_folium
from reservoir_data import choose_area
from shared_ui import choose_period, area_id, explain_errors
from map_tools import boundaries, colour_map
from region_tools import clicked_area
from weather_stats import PROPERTIES

st.title('Region map')
st.write('Click inside an outlined area. Its selection is shared with the other pages.')
series = choose_area(default_kind='EL',default_number=3)
start, end = choose_period(series)
kind = str(series.area_type.iloc[0])
mode = st.selectbox('Colour by',['Price area','Water area','Weather property'])
property_name = st.selectbox('Weather property',list(PROPERTIES)[:2],format_func=lambda x:PROPERTIES[x][0],disabled=mode!='Weather property')
with explain_errors():
    areas = boundaries(kind)
    colour_kind = {'Price area':'EL','Water area':'VASS','Weather property':'Weather'}[mode]
    with st.spinner('Preparing the map…'):
        figure, missing = colour_map(areas,colour_kind,property_name,start,end,area_id(series))
    event = st_folium(figure,height=590,use_container_width=True,key=f'map_{kind}',
                      returned_objects=['last_clicked','last_object_clicked'])
    click = event.get('last_clicked') or event.get('last_object_clicked')
    if click:
        token = (kind,click['lat'],click['lng'])
        if st.session_state.get('last_map_click') != token:
            st.session_state['last_map_click'] = token
            chosen = clicked_area(areas,click['lat'],click['lng'])
            if chosen is not None:
                st.session_state['selected_area_type'] = chosen.area_type
                st.session_state['selected_area_number'] = int(chosen.area_number)
                st.rerun()
    st.caption(f'Selected: {area_id(series)} · dark-green outline · {start} to {end}')
    if missing:
        st.info('Grey areas have no prepared weather: '+', '.join(missing))
st.caption('Price and water colours identify regions; they are not electricity prices. Weather uses a time mean for temperature and a time total for precipitation.')
