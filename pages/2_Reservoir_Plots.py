import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from reservoir_data import choose_area, METRICS, reservoir_plot

st.title("Megasinstatstikk Data Filter")
series = choose_area()
months = series.index.to_period("M").unique().sort_values().astype(str).tolist()
first, last = st.select_slider("Months", options=months, value=(months[0], months[0]))
column = st.selectbox("Measure", [*METRICS, "All measures"],
                      format_func=lambda name: METRICS.get(name, name))
periods = series.index.to_period("M")
selected = series.loc[(periods >= pd.Period(first)) & (periods <= pd.Period(last))]
if selected.empty:
    st.info("No reported observations in these months.")
    st.stop()
fig = reservoir_plot(selected, column)
st.pyplot(fig)
plt.close(fig)
st.caption("All measures uses min–max scaling over the selected interval; constant measures appear at zero.")
st.caption("NVE returns the full dataset. The slider filters the downloaded observations locally.")
