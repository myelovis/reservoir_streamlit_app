import streamlit as st

st.set_page_config(page_title='Chronological Insights · Norway',page_icon='🌊',layout='wide')


def home():
    st.title('Chronological Insights · Norway')
    st.caption('Magasinstatistikk · Open-Meteo / ERA5 · ENTSO-E')
    st.write('Choose an area on the map, then use the shared region and dates across pages.')
    st.page_link('pages/0_Region_Map.py',label='Select region and dates →')
    columns = st.columns(3)
    groups = [
        ('Explore', [('pages/1_Reservoir_Table.py','Reservoir table'),
                     ('pages/2_Reservoir_Plots.py','Reservoir plots'),
                     ('pages/5_Electricity_Transfers.py','Electricity transfers'),
                     ('pages/3_Reservoir_Patterns.py','STL and spectrogram')]),
        ('Diagnose', [('pages/4_Weather_Outliers.py','Weather · SATV / SPC / LOF'),
                      ('pages/8_Autocorrelation.py','ACF and PACF'),
                      ('pages/6_Weather_Correlation.py','Sliding window correlation')]),
        ('Forecast', [('pages/7_Filling_Forecast.py','Reservoir · SARIMAX / Ridge')]),
    ]
    for column, (title, links) in zip(columns, groups):
        with column.container(border=True):
            st.subheader(title)
            for path, label in links:
                st.page_link(path,label=label)
    st.caption('Plots read saved Atlas data. Currency data and electricity forecasts are planned; they are not included in this version.')


page = st.navigation({
    'Start':[st.Page(home,title='Home',default=True),st.Page('pages/0_Region_Map.py',title='Map and selectors')],
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
