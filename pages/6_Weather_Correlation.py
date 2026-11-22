from popup_ui import in_popup, page_title, settings
import streamlit as st
from reservoir_data import choose_area
from weather_data import load_period
from weather_stats import PROPERTIES, combine_weekly, sliding_correlation
from shared_ui import choose_period, area_id, explain_errors
from plot_tools import correlation_plot

page_title('Weather and reservoir correlation')
series = choose_area(default_kind='EL',default_number=3)
start, end = choose_period(series)
with explain_errors():
    weather, source = load_period(area_id(series),start,end)
    frame = combine_weekly(series.fill_ratio,weather).loc[str(start):str(end)]
    with settings('Correlation settings'):
        property_name = st.selectbox('Weather property',list(weather.columns),format_func=lambda x:PROPERTIES[x][0],
                                     help='Weekly temperature is averaged and weekly precipitation is summed.')
        target = st.selectbox('Reservoir variable',['filling_change','filling'],
                              format_func=lambda x:'Weekly filling change (pp)' if x=='filling_change' else 'Filling (%)',
                              help='Weekly change shows how much filling rose or fell. Filling shows the level.')
        left, right = st.columns(2)
        lag = left.slider('Weather leads filling by (weeks)',0, 12, 1,
                          help='For a one-week lead, compare this week’s filling with the previous week’s weather.')
        window = right.slider('Window length (weeks)',4, 52, min(12, max(4, len(frame) - 2)),
                              help='Short windows reveal local changes. Longer windows give smoother estimates.')
    result = sliding_correlation(frame,property_name,target,lag,window)
    if result.correlation.notna().sum()==0:
        st.info('No complete windows. Choose a longer shared time frame or check missing weeks.')
    figure = correlation_plot(result)
    if in_popup():
        figure.update_layout(height=445)
    st.plotly_chart(figure,width='stretch')
    st.caption(source)
    st.caption('Positive lag uses earlier weather. Partial weather weeks are excluded. Missing weeks are not filled. Correlation is not proof of prediction.')
    with st.expander('Correlation values'):
        st.dataframe(result.tail(20),height=220,width='stretch')
    st.download_button('Download correlation',result.to_csv().encode(),'rolling_correlation.csv','text/csv')
