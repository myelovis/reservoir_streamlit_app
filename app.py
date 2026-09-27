import streamlit as st

st.set_page_config(
    page_page_title="Hydropower Reservoir Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌊 Norwegian Hydropower Reservoirs Dashboard")
st.subheader("IND320-1 Data til Beslutning — Project Part 1")

st.markdown(
    """
    Welcome to the Hydropower Reservoir Monitoring Application!
    
    This app provides data visualization and analytics on Norwegian hydropower reservoir fill levels and capacity data.
    
    ### 📌 Navigation
    Use the sidebar menu on the left to navigate between pages:
    * **Home**: Project overview and system introduction.
    * **Page 1 - Data Overview**: Tabular view of reservoir metrics with embedded line charts.
    * **Page 2 - Interactive Visualizations**: Detailed trend analysis with dynamic subset filtering.
    * **Page 3 - Summary & Analytics**: Aggregated insights and metric distributions.
    """
)

# Sidebar navigation info
st.sidebar.title("Navigation")
st.sidebar.info("Select a page above to explore the data.")