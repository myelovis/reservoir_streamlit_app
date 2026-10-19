import streamlit as st

st.set_page_config(page_title="Reservoirs and Electricity", layout="wide")


def home():
    st.title("🌊 Norwegian Hydropower and Electricity Dashboard")
    st.subheader("IND320-1 Data til Beslutning — Project Parts 1 & 2")

    st.markdown("""
    Explore Norway’s reservoir storage and electricity transfers
    between Norway NO2 and Denmark DK1.

    ### Data sources
    - **NVE Magasinstatistikk:** reservoir filling, capacity and stored energy.
    - **ENTSO-E:** electricity imports and exports.

    ### Navigation
    - **Megasinstatistikk Data Overview:** reservoir tables and sparklines.
    - **Megasinstatistikk Data Filter:** select areas, months and measures.
    - **Entsoe Electric Transfer Report:** annual transfer energy and power-flow charts.

    Reservoir filling values are fractions: **0.60 means 60%**.
    Electricity transfers are exchanges between countries, not domestic production.
    """)


page = st.navigation([
    st.Page(home, title="Home", default=True),
    st.Page(
        "pages/1_Reservoir_Table.py",
        title="Megasinstatistikk Data Overview",
    ),
    st.Page(
        "pages/2_Reservoir_Plots.py",
        title="Megasinstatistikk Data Filter",
    ),
    st.Page(
        "pages/3_Electricity_Transfers.py",
        title="Entsoe Electric Transfer Report",
    ),
])

st.sidebar.info("Select a page above to explore the data.")

page.run()
