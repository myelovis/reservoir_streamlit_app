import streamlit as st

st.set_page_config(page_title="Reservoirs and Electricity", layout="wide")

page = st.navigation([
    st.Page("pages/1_Reservoir_Table.py",
            title="Megasinstatistikk Data Overview", default=True),
    st.Page("pages/2_Reservoir_Plots.py",
            title="Megasinstatistikk Data Filter"),
    st.Page("pages/3_Electricity_Transfers.py",
            title="Entsoe Electric Transfer Report"),
])
page.run()

st.title("🌊 Norwegian Hydropower Reservoirs Dashboard")
st.subheader("IND320-1 Data til Beslutning — Project Part 1")

st.markdown(
    """
    Welcome to the Hydropower Reservoir Monitoring Application!
    
    This app provides data visualization and analytics on Norwegian hydropower reservoir fill levels and capacity data.
    
    ### 📌 Navigation
    Use the sidebar menu on the left to navigate between pages:
    * **Home**: Project overview and system introduction.
    * **Page 1 - Data Overview**: Megasinstatistikk Reservoir metrics with embedded line charts.
    * **Page 2 - Interactive Visualizations**: Detailed trend analysis with Megasinstatistikk Reservoir.
    * **Page 3 - Summary & Analytics**: EntsoE Data.
    """
)

# Sidebar navigation info
st.sidebar.title("Navigation")
st.sidebar.info("Select a page above to explore the data.")
