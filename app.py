import streamlit as st

st.set_page_config(page_title='Reservoirs',page_icon='🌊',layout='wide')


def home():
    st.title('Reservoirs')
    st.write('Norwegian reservoir filling, weather and electricity transfers.')
    st.markdown('1. Choose an area on the **Map**.\n2. Set the shared time frame.\n3. Explore patterns, weather links or a filling forecast.')
    st.caption('NVE reservoir observations and ERA5 historical weather are read from MongoDB Atlas. Weather shows its sample count. Future weather uses an explicit assumption.')


page = st.navigation({
    'Explore':[st.Page(home,title='Home',default=True),st.Page('pages/0_Region_Map.py',title='Map')],
    'Reservoirs':[st.Page('pages/1_Reservoir_Table.py',title='Overview'),
                  st.Page('pages/2_Reservoir_Plots.py',title='Plots'),
                  st.Page('pages/3_Reservoir_Patterns.py',title='Patterns'),
                  st.Page('pages/7_Filling_Forecast.py',title='Forecast')],
    'Weather':[st.Page('pages/4_Weather_Outliers.py',title='Outliers'),
               st.Page('pages/6_Weather_Correlation.py',title='Correlation')],
    'Electricity':[st.Page('pages/5_Electricity_Transfers.py',title='Transfers')],
})
page.run()
