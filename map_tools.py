"""Build a small Folium map. Clicks are checked against real polygons."""
import folium
from branca.element import Element
import branca.colormap as cm
import numpy as np
import streamlit as st
from region_tools import read_areas
from weather_data import load_period
from weather_stats import PROPERTIES
from api_data import ApiDataError
from ui_feedback import fetch_progress

PALETTE = ['#287451','#549366','#78ad87','#a0c6a4','#386b4c']


@st.cache_data(show_spinner=False)
def boundaries(kind):
    return read_areas(kind)


@st.cache_data(show_spinner=False)
def display_boundaries(kind):
    areas = boundaries(kind).to_crs(3035)
    areas.geometry = areas.geometry.simplify(250, preserve_topology=True)
    return areas.to_crs(4326)


def colour_map(outlines, colour_kind, property_name, start, end, selected):
    outlines = display_boundaries(str(outlines.area_type.iloc[0]))
    shaded = display_boundaries(colour_kind).copy() if colour_kind in ('EL','VASS') else outlines.copy()
    legend, missing = None, []
    if colour_kind == 'Weather':
        st.caption('Weather shading estimates the regional value from five fixed sample points per area.')
        values = []
        with fetch_progress("Open-Meteo map weather") as update:
            for index, area in enumerate(shaded.itertuples()):
                def report(percent, stage):
                    update(round((index + percent / 100) * 100 / len(shaded)), stage)

                try:
                    data, _ = load_period(area.area_id, start, end, update=report)
                    values.append(float(getattr(data[property_name], PROPERTIES[property_name][2])()))
                except ApiDataError:
                    values.append(np.nan)
                    missing.append(area.area_id)
            if missing:
                update(99, "Map ready with unavailable areas marked")
            else:
                update(99, "Preparing map colours")
        finite = [value for value in values if np.isfinite(value)]
        low, high = (min(finite),max(finite)) if finite else (0,1)
        legend = cm.LinearColormap(['#edf6ee','#8aba94','#205b3d'],vmin=low,vmax=max(high,low+1e-6))
        legend.caption = f'{PROPERTIES[property_name][0]} ({PROPERTIES[property_name][1]})'
        shaded['colour'] = [legend(value) if np.isfinite(value) else '#e1e9e2' for value in values]
        shaded['value'] = [f'{value:.2f}' if np.isfinite(value) else 'No data' for value in values]
    else:
        shaded['colour'] = [PALETTE[i%len(PALETTE)] for i in range(len(shaded))]
        shaded['value'] = shaded['name']
    bounds = outlines.total_bounds
    result = folium.Map(location=[65,13],zoom_start=4,tiles=None)
    result.get_root().header.add_child(Element("""
        <style>
            .leaflet-container { background: #edf4ed; border-radius: 8px; }
            .leaflet-bar a, .leaflet-bar a:hover { background: #f7faf7; color: #295b44; }
            .leaflet-control-attribution a { color: #295b44; }
        </style>
    """))
    folium.GeoJson(shaded.to_json(),style_function=lambda f:{
        'fillColor':f['properties']['colour'],'fillOpacity':.38,'weight':0}).add_to(result)
    folium.GeoJson(outlines.to_json(),style_function=lambda f:{
        'color':'#0b3823' if f['properties']['area_id']==selected else '#4a7358',
        'weight':4 if f['properties']['area_id']==selected else 1.2,'fillOpacity':0}).add_to(result)
    result.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]])
    if legend:
        legend.add_to(result)
    return result, missing, shaded[["name", "value"]]
