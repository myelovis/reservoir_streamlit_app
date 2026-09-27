import matplotlib.pyplot as plt
import streamlit as st
from utils import load_data

st.set_page_config(page_title="Summary & Analytics", page_icon="📋", layout="wide")

st.title("📋 Dataset Distributions & Summary Analytics")

try:
    df = load_data()

    st.subheader("Statistical Summary")
    st.dataframe(df.describe(), use_container_width=True)

    st.subheader("Global Metric Histograms")
    fig, ax = plt.subplots(figsize=(12, 8))
    df.hist(ax=ax, figsize=(12, 8))
    plt.tight_layout()
    st.pyplot(plt.gcf())

except Exception as e:
    st.error(f"Error loading summary page: {e}")