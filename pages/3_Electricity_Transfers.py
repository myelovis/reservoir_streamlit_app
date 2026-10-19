import calendar
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from transfer_data import load_transfers
from transfer_plots import annual_totals, energy_donut, power_lines

st.set_page_config(page_title="Electricity Transfers", layout="wide")
st.title("Norway–Denmark electricity transfers")
st.caption("ENTSO-E → Spark → Cassandra → Spark → MongoDB → Streamlit")
st.caption("Streamlit reads nve.simple_transfers, published by notebook section 6.2.")
if st.button("Refresh transfer data"):
    load_transfers.clear()
try:
    df = load_transfers()
except (KeyError, FileNotFoundError):
    st.info("Add MONGO_URI to Streamlit Secrets before opening the transfer data.")
    st.stop()
except Exception:
    st.error("MongoDB could not be read. Check the Atlas URI, database-user permissions and network access.")
    st.stop()
if df.empty:
    st.info("No NO2–DK1 records found in the last two years. Run notebook sections 4–6.2 to publish them.")
    st.stop()

st.caption(f"Available observations: {df.time.min():%Y-%m-%d} to {df.time.max():%Y-%m-%d} (UTC).")
left, right = st.columns(2)
with left:
    connection = st.radio("Connection", sorted(df.connection.unique()))
    connection_df = df.loc[df.connection.eq(connection)]
    years = sorted(connection_df.year.unique(), reverse=True)
    completed = pd.Timestamp.now(tz="Europe/Oslo").year - 1
    default = years.index(completed) if completed in years else 0
    year = int(st.selectbox("Year", years, index=default))
    annual = connection_df.loc[connection_df.year.eq(year)]
    totals = annual_totals(annual, year)
    st.dataframe(totals.rename(index={"in":"Into Norway", "out":"Out of Norway"}), width="stretch")
    if len(totals) < 2 or (totals.coverage_pct < 99.999).any():
        st.warning("Incomplete annual coverage. The chart shows reported totals, not a complete annual balance.")
    if (totals.coverage_pct > 100.001).any():
        st.warning("Coverage exceeds 100%. Check the notebook output for overlapping or duplicate intervals.")
    if totals.energy_mwh.sum() > 0:
        fig = energy_donut(totals, year)
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("No positive reported energy to plot for this year.")

with right:
    months = st.pills("Months", list(range(1, 13)), selection_mode="multi",
                      default=[1], format_func=lambda m: calendar.month_abbr[m])
    st.caption(f"Selected year: {year}. January is the notebook's default analysis month.")
    if months and annual.time.dt.tz_convert("Europe/Oslo").dt.month.isin(months).any():
        fig = power_lines(annual, months)
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Select months with reported observations.")

with st.expander("Data source and method"):
    st.markdown("""
    **Source:** ENTSO-E physical flows for Norway NO2 ↔ Denmark DK1.
    The notebook fetches the last two years, writes intervals to Cassandra using Spark,
    reads relevant columns back using Spark, and upserts them into MongoDB.

    **Units:** power is MW; energy is MWh. Each interval contributes MW × hours.
    Imports and exports are electricity transfers, not domestic production.
    Year and month selections use Europe/Oslo, as in the notebook.

    **Coverage:** reported hours are compared with the complete calendar year
    (8,760 hours, or 8,784 in a leap year). Missing periods are not filled with zero.
    The lines show measured intervals without bridging gaps or unselected months.

    **Publication:** MongoDB upserts are batched, not an atomic snapshot. Refresh after
    the notebook finishes and confirms its saved record count. This example covers
    one international connection, not all Norwegian imports and exports.
    """)
    st.link_button("ENTSO-E API reference", "https://documenter.getpostman.com/view/7009892/2s93JtP3F6")
st.subheader("Spark-extracted records")
st.dataframe(annual.head(100), width="stretch")
