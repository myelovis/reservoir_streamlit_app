from datetime import date
import matplotlib.pyplot as plt
import streamlit as st
from reservoir_data import choose_area
from weather_data import load_weather
from atlas_data import AtlasSetupError, DatasetNotReady
from pymongo.errors import PyMongoError
from analysis import precipitation_spc, temperature_lof

st.title("Weather Outliers")
st.write("Explore unusual precipitation and temperature in hourly ERA5 regional averages.")
series = choose_area(default_kind="EL", default_number=3)
kind, number = series.area_type.iloc[0], int(series.area_number.iloc[0])
if kind != "EL":
    st.info("Select area type EL to analyse ERA5 electricity-area data. National and watercourse boundaries use different definitions; their weather data is not substituted with NO3.")
    st.stop()
region_id = f"NO{number}"
year = int(st.number_input("Weather year (complete calendar year)", min_value=1940,
                           max_value=date.today().year - 1, value=2024, step=1))
dataset_key = f"{region_id}_{year}"
st.caption(f"Selected weather: {region_id} · {year} · ERA5 · UTC · temperature °C · precipitation mm/hour")

if st.button("Refresh weather from Atlas"):
    load_weather.clear()
try:
    weather, source = load_weather(region_id, year)
except (AtlasSetupError, DatasetNotReady) as error:
    st.info(str(error))
    st.stop()
except PyMongoError:
    st.error("Atlas weather could not be read. Check MONGO_URI, database-user permissions and Network Access.")
    st.stop()
except (ValueError, TypeError) as error:
    st.error(str(error))
    st.stop()
st.caption(source + " · full-year timestamp and finite-value checks passed")
left, middle, right = st.columns(3)
left.metric("Hourly observations", f"{len(weather):,}")
middle.metric("Mean temperature", f"{weather.temperature_2m.mean():.1f} °C")
right.metric("Annual mean-area precipitation", f"{weather.precipitation.sum():,.1f} mm")
st.download_button("Download selected weather averages", weather.assign(region_id=region_id).to_csv().encode(), f"{dataset_key}_era5.csv", "text/csv")
spc_tab, lof_tab = st.tabs(["Precipitation · SPC", "Temperature · LOF"])

with spc_tab:
    st.subheader("Precipitation outliers")
    left, right = st.columns(2)
    cutoff = left.number_input("DCT cutoff period (days)", min_value=1., max_value=365., value=30., step=1.)
    sigma = right.number_input("Robust standard deviations", min_value=.5, max_value=10., value=3., step=.5)
    try:
        fig, results, summary = precipitation_spc(weather, cutoff, sigma, region_id)
    except ValueError as error:
        st.warning(str(error))
    else:
        a, b, c = st.columns(3)
        a.metric("Outlier hours", f"{summary['outlier_hours']:,}")
        b.metric("Outlier share", f"{summary['outlier_percent']:.2f}%")
        c.metric("Robust sigma", f"{summary['robust_sigma']:.3f} mm")
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Median and normal-scaled MAD are estimated from the full year of DCT high-pass residuals. Residuals/SATV are not plotted; limits are translated back to precipitation units. Negative lower limits are statistical bounds, not negative rainfall.")
        outliers = results.loc[results.outlier]
        st.dataframe(outliers, width="stretch")
        st.download_button("Download precipitation outliers", outliers.to_csv().encode(), f"{dataset_key}_spc_outliers.csv", "text/csv")

with lof_tab:
    st.subheader("Temperature anomalies")
    left, right = st.columns(2)
    proportion = left.slider("Target anomaly proportion (%)", min_value=.1, max_value=10., value=1., step=.1) / 100
    neighbours = int(right.number_input("LOF neighbours", min_value=2, max_value=min(200, len(weather)-1), value=20, step=1))
    try:
        fig, results, summary = temperature_lof(weather, proportion, neighbours, region_id)
    except ValueError as error:
        st.warning(str(error))
    else:
        a, b = st.columns(2)
        a.metric("Anomaly hours", f"{summary['anomaly_hours']:,}")
        b.metric("Actual anomaly share", f"{summary['anomaly_percent']:.2f}%")
        st.pyplot(fig)
        plt.close(fig)
        st.caption("LOF compares neighbours in temperature-value space; it does not model seasonal or temporal context. The target proportion sets the threshold; ties can change the exact count. Flags indicate unusual values, not proven data errors.")
        anomalies = results.loc[results.anomaly]
        st.dataframe(anomalies, width="stretch")
        st.download_button("Download temperature anomalies", anomalies.to_csv().encode(), f"{dataset_key}_lof_anomalies.csv", "text/csv")
