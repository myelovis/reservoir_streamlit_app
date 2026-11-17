from pathlib import Path
import streamlit as st
import matplotlib as mpl
from cycler import cycler

mpl.rcParams['axes.prop_cycle'] = cycler(color=['#205b3d','#57966b','#89af91','#103e2a','#b6d1ba'])

st.set_page_config(page_title='Chronological Insights · Norway',page_icon='🌿',layout='wide')
style = (Path(__file__).parent / 'style.css').read_text(encoding='utf-8')
st.html(f'<style>{style}</style>')


def home():
    # One small botanical accent; the rest of the page stays plain.
    st.html('''<div class="brand-label">
        <svg class="brand-leaf" viewBox="0 0 48 48" aria-hidden="true" fill="none">
            <path d="M12 39C17 27 27 15 37 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M17 30C6 29 8 17 10 14C18 17 22 23 17 30Z" fill="#e0ece1" stroke="currentColor" stroke-width="1.2"/>
            <path d="M24 22C24 10 33 6 39 6C40 16 34 23 24 22Z" fill="#edf4ed" stroke="currentColor" stroke-width="1.2"/>
            <path d="M20 28C29 22 37 25 40 28C34 36 26 36 20 28Z" fill="#d1e3d4" stroke="currentColor" stroke-width="1.2"/>
        </svg>
        <span>NORWAY / WATER · WEATHER · ENERGY</span>
    </div>''')
    st.title('Chronological Insights')
    st.write('Understand the past. Explore what comes next.')
    st.caption('[Magasinstatistikk](https://biapi.nve.no/magasinstatistikk/swagger/index.html) · '
               '[Open-Meteo / ERA5](https://open-meteo.com/en/docs/historical-weather-api) · '
               '[ENTSO-E](https://transparencyplatform.zendesk.com/hc/en-us/articles/15692855254548-Sitemap-for-Restful-API-Integration)')
    if st.button('Select region and dates →', type='primary'):
        from region_picker import open_region_picker
        open_region_picker()
    st.caption('One shared region and time frame across your analyses.')
    st.space('small')
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
                st.page_link(path,label=label,icon=':material/arrow_outward:')
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
