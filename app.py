from pathlib import Path
import streamlit as st
import matplotlib as mpl
from cycler import cycler

mpl.rcParams['axes.prop_cycle'] = cycler(color=['#205b3d','#57966b','#89af91','#103e2a','#b6d1ba'])

st.set_page_config(page_title='Chronological Insights · Norway',page_icon='🌿',layout='wide')
style = (Path(__file__).parent / 'style.css').read_text(encoding='utf-8')
st.html(f'<style>{style}</style>')


def home():
    # Use an image file so the leaf renders reliably.
    with st.container(key='home_heading'):
        heading, accent = st.columns([9, 1], vertical_alignment='center')
        with heading:
            st.caption('NORWAY / WATER · WEATHER · ENERGY')
            st.title('Chronological Insights')
        with accent:
            leaf = Path(__file__).parent / 'leaf.jpg'
            if not leaf.exists():
                leaf = leaf.with_suffix('.svg')
            if leaf.exists():
                st.image(str(leaf), width=58)
    st.write('Understand the past. Explore what comes next.')
    st.caption('[Magasinstatistikk](https://biapi.nve.no/magasinstatistikk/swagger/index.html) · '
               '[Open-Meteo / ERA5](https://open-meteo.com/en/docs/historical-weather-api) · '
               '[ENTSO-E](https://transparencyplatform.zendesk.com/hc/en-us/articles/15692855254548-Sitemap-for-Restful-API-Integration)')
    if st.button('Select region and dates →', type='primary'):
        st.session_state.pop('analysis_popup_label', None)
        from region_picker import open_region_picker
        open_region_picker()
    columns = st.columns(3)
    groups = [
        ('Explore', [('pages/1_Reservoir_Table.py','Reservoir table'),
                     ('pages/2_Reservoir_Plots.py','Reservoir plots'),
                     ('pages/5_Electricity_Transfers.py','Electricity transfers'),
                     ('pages/3_Reservoir_Patterns.py','STL and spectrogram')]),
        ('Diagnose', [('pages/4_Weather_Outliers.py','Weather outliers'),
                      ('pages/8_Autocorrelation.py','ACF and PACF'),
                      ('pages/6_Weather_Correlation.py','Sliding window correlation')]),
        ('Forecast', [('pages/7_Filling_Forecast.py','Reservoir forecast')]),
    ]
    for column, (title, links) in zip(columns, groups):
        with column.container(border=True, key=f'home_{title.lower()}'):
            st.caption({'Explore':'01 / OBSERVE','Diagnose':'02 / UNDERSTAND','Forecast':'03 / LOOK AHEAD'}[title])
            st.subheader(title)
            st.write({'Explore':'Reservoirs, weather and energy over time.',
                      'Diagnose':'Patterns, unusual values and relationships.',
                      'Forecast':'Future filling with SARIMAX or Ridge.'}[title])
            for path, label in links:
                if st.button(label, icon=':material/arrow_outward:', key=f'open_{label}', type='tertiary', width='stretch'):
                    st.session_state['analysis_popup_label'] = label
    if st.session_state.get('analysis_popup_label'):
        from analysis_popup import open_analysis
        open_analysis(st.session_state['analysis_popup_label'])
    st.caption('NVE · ERA5 · ENTSO-E / Saved observations from MongoDB Atlas')


page = st.navigation({
    'Start':[st.Page(home,title='Home',default=True)],
    'Explore':[st.Page('pages/1_Reservoir_Table.py',title='Reservoir overview'),
                  st.Page('pages/2_Reservoir_Plots.py',title='Plots'),
                  st.Page('pages/3_Reservoir_Patterns.py',title='STL and spectrogram'),
                  st.Page('pages/5_Electricity_Transfers.py',title='Electricity transfers')],
    'Diagnose':[st.Page('pages/4_Weather_Outliers.py',title='Weather outliers'),
                st.Page('pages/8_Autocorrelation.py',title='ACF and PACF'),
                st.Page('pages/6_Weather_Correlation.py',title='Sliding correlation')],
    'Forecast':[st.Page('pages/7_Filling_Forecast.py',title='Reservoir forecast')],
})
page.run()
