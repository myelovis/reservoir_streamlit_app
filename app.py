import streamlit as st

st.set_page_config(page_title="Reservoirs and Electricity", layout="wide")


def home():
    st.title("🌊 Norwegian Hydropower and Electricity Dashboard")
    st.subheader("IND320-1 Data til Beslutning — Project Parts 1–3")

    st.markdown("""
    Explore Norway’s reservoir storage and electricity transfers
    between Norway NO2 and Denmark DK1.

    ### Plot data: MongoDB Atlas
    - **Reservoirs:** NVE observations published to `nve.reservoir_weekly`.
    - **Electricity transfers:** published Part 2 records in `nve.simple_transfers`.
    - **Weather:** existing ERA5 regional averages in `nve.era5_hourly`. No CSV files or new API downloads are needed for plots.

    ### Navigation
    - **Reservoir Overview / Reservoir Plots:** tables, area selection and measures.
    - **Reservoir Patterns:** STL decomposition and spectrogram tabs.
    - **Weather Outliers:** precipitation SPC and temperature LOF tabs.
    - **Electricity Transfers:** annual transfer energy and power-flow charts.

    Reservoir filling values are fractions: **0.60 means 60%**.
    Electricity transfers are exchanges between countries, not domestic production.
    """)


page = st.navigation({
    "Start": [st.Page(home, title="Home", default=True)],
    "Reservoirs": [st.Page(
        "pages/1_Reservoir_Table.py",
        title="Reservoir Overview",
    ),
    st.Page(
        "pages/2_Reservoir_Plots.py",
        title="Reservoir Plots",
    ),
    st.Page("pages/4_Reservoir_Patterns.py", title="Reservoir Patterns")],
    "Weather": [st.Page("pages/5_Weather_Outliers.py", title="Weather Outliers")],
    "Electricity": [
    st.Page(
        "pages/3_Electricity_Transfers.py",
        title="Electricity Transfers",
    ),
    ],
})


page.run()
