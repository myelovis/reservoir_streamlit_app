from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app_data(monkeypatch):
    import reservoir_data, weather_data
    dates = pd.date_range('2022-01-02','2024-12-29',freq='7D')
    rows = []
    for kind,number in [('NO',0)]+[('EL',i) for i in range(1,6)]+[('VASS',i) for i in range(1,4)]:
        for i,date in enumerate(dates):
            rows.append(dict(date_id=date,area_type=kind,area_number=number,
                              fill_ratio=.6+.1*np.sin(i/8),capacity_twh=10.,storage_twh=6.,
                              fill_ratio_previous_week=.6,fill_ratio_change=.01))
    frame = pd.DataFrame(rows)
    hours = pd.date_range('2024-01-01','2025-01-01',freq='h',inclusive='left',tz='UTC')
    weather = pd.DataFrame({'temperature_2m':5+np.sin(np.arange(len(hours))/200),
                            'precipitation':.1+.09*np.sin(np.arange(len(hours))/23)},index=hours)
    monkeypatch.setattr(reservoir_data,'load_reservoirs',lambda:frame.copy())
    monkeypatch.setattr(weather_data,'load_weather',lambda region,year:(weather.copy(),'Test fixture, not live data'))
    monkeypatch.setattr(weather_data,'load_period',lambda region,start,end:(weather.loc[str(pd.Timestamp(start).date()):str(pd.Timestamp(end).date())].copy(),'Test fixture, not live data'))
    return frame,weather


def run_page(filename):
    app = AppTest.from_file(str(ROOT/'pages'/filename),default_timeout=45).run()
    assert not app.exception,app.exception
    return app


def test_temperature_default_and_property_controls(app_data):
    app = run_page('4_Weather_Outliers.py')
    properties = [item for item in app.selectbox if item.label=='Weather property']
    assert [item.value for item in properties]==['temperature_2m','temperature_2m']
    properties[0].set_value('precipitation').run()
    assert not app.exception
    properties = [item for item in app.selectbox if item.label=='Weather property']
    properties[1].set_value('precipitation').run()
    assert not app.exception


def test_correlation_controls(app_data):
    app = run_page('6_Weather_Correlation.py')
    next(x for x in app.slider if 'leads' in x.label).set_value(4).run()
    next(x for x in app.slider if 'Window length' in x.label).set_value(26).run()
    next(x for x in app.selectbox if x.label=='Weather property').set_value('precipitation').run()
    assert not app.exception
    from datetime import date
    selected=(date(2024,2,1),date(2024,12,1))
    app.date_input[0].set_value(selected).run()
    assert tuple(app.session_state['selected_period'])==selected


def test_map_click_updates_shared_area(app_data,monkeypatch):
    import streamlit_folium
    from region_tools import read_areas
    point = read_areas('EL').set_index('area_id').loc['NO1'].geometry.representative_point()
    monkeypatch.setattr(streamlit_folium,'st_folium',lambda *a,**k:{'last_clicked':{'lat':point.y,'lng':point.x}})
    app = run_page('0_Region_Map.py')
    assert app.session_state['selected_area_type']=='EL'
    assert app.session_state['selected_area_number']==1
    next(x for x in app.selectbox if x.label=='Colour by').set_value('Water area').run()
    assert not app.exception and len(app.warning)>0


def test_both_forecast_models(app_data):
    app = run_page('7_Filling_Forecast.py')
    next(x for x in app.button if x.label=='Forecast').click().run()
    assert not app.exception
    assert len(app.session_state['forecast_result'][2])==12
    next(x for x in app.radio if x.label=='Model').set_value('Ridge regression').run()
    app.multiselect[0].set_value(['temperature_2m'])
    next(x for x in app.button if x.label=='Forecast').click().run()
    assert not app.exception
    assert app.session_state['forecast_result'][0][-1]=='Ridge regression'
    assert len(app.session_state['forecast_result'][4])==12
    from datetime import date
    app.date_input[0].set_value((date(2024,11,25),date(2024,11,28))).run()
    next(x for x in app.button if x.label=='Forecast').click().run()
    assert not app.exception and any('24 weekly' in x.value for x in app.warning)


def test_missing_atlas_shows_help(monkeypatch):
    import reservoir_data
    from atlas_data import AtlasSetupError
    def unavailable():raise AtlasSetupError('Set MONGO_URI privately to continue.')
    monkeypatch.setattr(reservoir_data,'load_reservoirs',unavailable)
    app=run_page('6_Weather_Correlation.py')
    assert len(app.info)==1
    assert 'MONGO_URI' in app.info[0].value


def test_main_navigation_starts_on_home():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
    assert not app.exception
    assert app.title[0].value=='Reservoirs'

