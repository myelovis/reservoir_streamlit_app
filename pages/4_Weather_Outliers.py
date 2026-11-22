from popup_ui import in_popup, page_title, settings
import pandas as pd
import streamlit as st
from reservoir_data import choose_area
from weather_data import load_weather, weather_years
from weather_stats import PROPERTIES, spc, lof
from plot_tools import weather_plot
from shared_ui import choose_period, area_id, explain_errors

page_title('Weather outliers')
series = choose_area(default_kind='EL',default_number=3)
start, end = choose_period(series, weather_dates=True)
with explain_errors():
    years = [year for year in weather_years(area_id(series)) if start.year <= year <= end.year]
    if not years:
        st.info('No complete ERA5 archive year is available for this selection. Change the dates on Home.')
        st.stop()
    year = st.selectbox('Analysis year', years, index=len(years)-1,
                        help='Analyse one year at a time. SPC limits use that complete year.')
    weather, source = load_weather(area_id(series), year)
    st.caption(source)
    st.caption(f'Limits use the complete year {year}. Plots show its overlap with the shared time frame.')
    spc_tab, lof_tab = st.tabs(['DCT / SPC','LOF'])
    for tab, method in [(spc_tab,'SPC'),(lof_tab,'LOF')]:
        with tab:
            with settings(f'{method} settings'):
                with st.form(f'analysis_{method}'):
                    prop = st.selectbox('Weather property',list(weather.columns),key=f'property_{method}',format_func=lambda x:PROPERTIES[x][0])
                    name, unit, _ = PROPERTIES[prop]
                    left, right = st.columns(2)
                    if method=='SPC':
                        cutoff = left.number_input('DCT cutoff (days)',1.,365.,30.,key='cutoff')
                        multiplier = right.number_input('Robust standard deviations',.5,10.,3.,step=.5)
                        calculation = st.cache_data(ttl=3600,max_entries=16,show_spinner=False)(spc)
                        st.caption('Filtered residuals are used for limits and flags; they are not plotted. The default property is temperature.')
                    else:
                        share = left.slider('Target anomalies (%)',.1,10.,1.,step=.1)/100
                        neighbours = right.number_input('Neighbours',2,min(200,len(weather)-1),20)
                        calculation = st.cache_data(ttl=3600,max_entries=16,show_spinner=False)(lof)
                        st.caption('LOF compares values with nearby values. A flag is not proof of a data error.')
                    run = st.form_submit_button(f'Run {method}')
            context = (area_id(series), year, prop)
            key = f'weather_result_{method}'
            if run:
                with st.spinner('Finding unusual values…'):
                    result = (calculation(weather[prop], cutoff, multiplier) if method == 'SPC'
                              else calculation(weather[prop], share, neighbours))
                st.session_state[key] = (context, result)
            saved = st.session_state.get(key)
            if saved is None or saved[0] != context:
                st.info(f'Choose settings and click Run {method}.')
                continue
            result = saved[1]
            visible = result.loc[str(start):str(end)]
            if in_popup():
                st.caption(f'{int(visible.flag.sum())} flagged hours · {visible.flag.mean()*100:.2f}% in view')
            else:
                a,b = st.columns(2)
                a.metric('Flagged hours in view',int(visible.flag.sum()))
                b.metric('Flagged share in view',f'{visible.flag.mean()*100:.2f}%' if len(visible) else 'No overlap')
            figure = weather_plot(visible,f'{area_id(series)} · {name} · {method}',unit)
            if in_popup():
                figure.update_layout(height=280, margin=dict(t=40,b=45))
            st.plotly_chart(figure,width='stretch')
            with st.expander('Flagged hours'):
                st.dataframe(visible.loc[visible.flag],height=220,width='stretch')
            st.download_button('Download flags',visible.loc[visible.flag].to_csv().encode(),f'{prop}_{method}.csv','text/csv',key=f'download_{method}')
