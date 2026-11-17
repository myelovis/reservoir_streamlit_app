import pandas as pd
import streamlit as st
from reservoir_data import choose_area
from weather_data import load_period
from weather_stats import PROPERTIES, weekly_weather
from shared_ui import choose_period, area_id, explain_errors
from forecast_tools import future_weather, sarimax_forecast, ridge_forecast
from plot_tools import forecast_animation


@st.cache_data(ttl=1800,max_entries=12,show_spinner=False)
def fit_model(model,y,steps,parameters,exog,future):
    function = sarimax_forecast if model=='SARIMAX' else ridge_forecast
    return function(y,steps=steps,exog=exog,future_exog=future,**parameters)


st.title('Filling forecast')
series = choose_area(default_kind='EL',default_number=3)
start, end = choose_period(series)
st.caption('The shared time frame is the training period. Forecasts begin one week after its last observation.')
model = st.radio('Model',['SARIMAX','Ridge regression'],horizontal=True)
with st.form('forecast_controls'):
    left, right = st.columns(2)
    horizon = left.slider('Forecast horizon (weeks)',1,52,12)
    properties = right.multiselect('Weather inputs',list(PROPERTIES)[:2],key='forecast_weather',format_func=lambda x:PROPERTIES[x][0])
    if model=='SARIMAX':
        a,b,c = st.columns(3)
        order = (a.number_input('p',0,3,1),b.number_input('d',0,2,1),c.number_input('q',0,3,0))
        with st.expander('Seasonal and fit settings'):
            a,b,c,d = st.columns(4)
            seasonal = (a.number_input('P',0,2,0),b.number_input('D',0,1,0),c.number_input('Q',0,2,0),d.number_input('Season length',2,104,52))
            trend = st.selectbox('Trend',['n','c','t','ct'],format_func=lambda x:{'n':'None','c':'Constant','t':'Linear','ct':'Constant + linear'}[x])
            stationary = st.checkbox('Keep stationary AR terms',True)
            invertible = st.checkbox('Keep invertible MA terms',True)
            maxiter = st.slider('Maximum fit steps',20,200,100)
            confidence = st.slider('Conditional interval (%)',80,99,95)/100
        parameters = dict(order=order,seasonal=seasonal,trend=trend,stationary=stationary,
                          invertible=invertible,maxiter=maxiter,confidence=confidence)
    else:
        a,b = st.columns(2)
        parameters = dict(lags=a.slider('Past filling weeks',1,24,8),alpha=b.number_input('Ridge penalty',.01,100.,1.))
    scenario = st.selectbox('Future weather assumption',['Recent mean','Training seasonal mean','Upload CSV'])
    upload = st.file_uploader('Future weekly weather: date plus the selected property columns',type='csv')
    submitted = st.form_submit_button('Forecast',type='primary')

context = (area_id(series),str(start),str(end),model)
if submitted:
    with explain_errors():
        training = series.loc[str(start):str(end),'fill_ratio']*100
        training.index = pd.to_datetime(training.index,utc=True)
        training = training.sort_index().asfreq('7D')
        if len(training)<24:
            raise ValueError('Choose a training period with at least 24 weekly observations.')
        exog = future = None
        dates = pd.date_range(training.index[-1]+pd.Timedelta(days=7),periods=horizon,freq='7D')
        if properties:
            with st.spinner('Reading training weather…'):
                weather, _ = load_period(area_id(series),start,end)
                exog = weekly_weather(weather).reindex(training.index)[properties]
            if scenario=='Upload CSV':
                if upload is None:
                    raise ValueError('Upload one row per future week, or choose an assumption.')
                future = pd.read_csv(upload)
                if not {'date',*properties}.issubset(future.columns):
                    raise ValueError('The CSV needs a date column and every selected weather column.')
                future.index = pd.to_datetime(future.pop('date'),utc=True)
                future = future[properties].apply(pd.to_numeric)
                if not future.index.equals(dates):
                    raise ValueError('CSV dates must match every forecast week, in order.')
            else:
                future = future_weather(exog,dates,scenario)
        with st.spinner('Fitting the model…'):
            forecast, notes = fit_model(model,training,horizon,parameters,exog,future)
        st.session_state['forecast_result'] = (context,training,forecast,notes,future,scenario)

saved = st.session_state.get('forecast_result')
if saved and saved[0]==context:
    _, training, forecast, notes, future, scenario = saved
    for note in notes:
        st.warning(note)
    st.plotly_chart(forecast_animation(training.tail(104),forecast,f'{area_id(series)} · {model}'),width='stretch')
    if forecast.forecast.lt(0).any() or forecast.forecast.gt(100).any():
        st.warning('Some forecasts are outside 0–100%. They are shown as fitted; try a simpler model.')
    st.caption('Forecasts are recursive. Future observed filling is never used. Intervals, when shown, assume the future weather inputs are correct; they are not quantile-regression intervals.')
    if future is not None:
        with st.expander('Future weather used: '+scenario):
            st.dataframe(future,width='stretch')
    st.download_button('Download forecast',forecast.to_csv().encode(),'filling_forecast.csv','text/csv')
