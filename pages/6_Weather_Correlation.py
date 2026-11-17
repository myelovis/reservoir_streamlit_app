import streamlit as st
from reservoir_data import choose_area
from weather_data import load_period
from weather_stats import PROPERTIES, combine_weekly, sliding_correlation
from shared_ui import choose_period, area_id, explain_errors
from plot_tools import correlation_plot

st.title('Weather and reservoir correlation')
series = choose_area(default_kind='EL',default_number=3)
start, end = choose_period(series)
with explain_errors():
    with st.spinner('Matching hourly weather to weekly filling…'):
        weather, source = load_period(area_id(series),start,end)
        frame = combine_weekly(series.fill_ratio,weather).loc[str(start):str(end)]
    property_name = st.selectbox('Weather property',list(weather.columns),format_func=lambda x:PROPERTIES[x][0])
    target = st.selectbox('Reservoir variable',['filling_change','filling'],
                          format_func=lambda x:'Weekly filling change (pp)' if x=='filling_change' else 'Filling (%)')
    left, right = st.columns(2)
    lag = left.slider('Weather leads filling by (weeks)',0,12,1)
    window = right.slider('Window length (weeks)',4,52,12)
    result = sliding_correlation(frame,property_name,target,lag,window)
    if result.correlation.notna().sum()==0:
        st.info('No complete windows. Choose a longer shared time frame or check missing weeks.')
    st.plotly_chart(correlation_plot(result),width='stretch')
    st.caption(source)
    st.caption('Positive lag uses earlier weather. Partial weather weeks are excluded. Missing weeks are not filled. Correlation is not proof of prediction.')
    st.dataframe(result.tail(20),width='stretch')
    st.download_button('Download correlation',result.to_csv().encode(),'rolling_correlation.csv','text/csv')
