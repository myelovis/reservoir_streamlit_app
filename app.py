import streamlit as st

st.set_page_config(
    page_title="Reservoirs, Weather and Electricity",
    page_icon="🌊",
    layout="wide",
)


def home():
    st.title("🌊 Norwegian Reservoirs, Weather and Electricity")
    st.subheader("IND320 — Data til Beslutning · Project Parts 1–3")

    st.markdown("""
    Explore Norwegian reservoir filling, regional weather patterns,
    and electricity transfers between NO2 and Denmark DK1.

    ### Data sources

    All plot data is read from **MongoDB Atlas**:

    - **Reservoirs:** NVE observations in `nve.reservoir_weekly`.
    - **Weather:** ERA5 regional averages in `nve.era5_hourly`.
    - **Electricity transfers:** Part 2 records in `nve.simple_transfers`.

    ### Explore the dashboard

    - **Reservoir Overview:** tables and sparklines.
    - **Reservoir Plots:** select areas, months and measurements.
    - **Reservoir Patterns:** STL decomposition and spectrogram.
    - **Weather Outliers:** precipitation SPC and temperature LOF.
    - **Electricity Transfers:** import/export summaries and flow charts.

    Reservoir tables use filling fractions: **0.60 means 60%**.
    STL analysis displays filling percentages.

    Electricity transfers represent exchanged electricity,
    not domestic production.
    """)

    st.info(
        "For the verified ERA5 weather dataset, select "
        "area type EL, area number 3, and year 2024."
    )


navigation = st.navigation({
    "Start": [
        st.Page(home, title="Home", default=True),
    ],
    "Reservoirs": [
        st.Page(
            "pages/1_Reservoir_Table.py",
            title="Reservoir Overview",
        ),
        st.Page(
            "pages/2_Reservoir_Plots.py",
            title="Reservoir Plots",
        ),
        st.Page(
            "pages/3_Reservoir_Patterns.py",
            title="Reservoir Patterns",
        ),
    ],
    "Weather": [
        st.Page(
            "pages/4_Weather_Outliers.py",
            title="Weather Outliers",
        ),
    ],
    "Electricity": [
        st.Page(
            "pages/5_Electricity_Transfers.py",
            title="Electricity Transfers",
        ),
    ],
})

navigation.run()
