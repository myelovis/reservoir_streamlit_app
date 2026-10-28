from datetime import date
import matplotlib.pyplot as plt
import streamlit as st
from reservoir_data import choose_area
from weather_data import load_weather, prepare_weather
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

with st.expander("Load weather data", expanded=False):
    st.write(f"Reuse the notebook's regional_hourly_mean.csv for **{region_id}, {year}**, or prepare new data through the ERA5 module. Upload regional averages, not an individual cell file.")
    version_key = f"upload_version_{dataset_key}"
    upload_version = st.session_state.get(version_key, 0)
    upload = st.file_uploader(f"ERA5 regional-average CSV for {region_id}, {year}", type=["csv"], key=f"upload_{dataset_key}_{upload_version}")
    uploads = st.session_state.setdefault("weather_uploads", {})
    if upload is not None:
        uploads[dataset_key] = upload.getvalue()
    if dataset_key in uploads and st.button("Use server export instead", key=f"clear_{dataset_key}"):
        del uploads[dataset_key]
        st.session_state[version_key] = upload_version + 1
        st.rerun()
    st.caption("A CSV without a region_id column is treated as your labelled upload for the region shown above; verify its origin. Saved files and uploads are kept separate for every region and year.")
    if st.button(f"Fetch {region_id} ERA5 for {year}", key=f"fetch_{dataset_key}"):
        try:
            with st.spinner("Preparing 1,000 sampled locations and fetching ERA5. This can take a long time; API quotas apply. Completed cells are reused on retry."):
                prepare_weather(region_id, year)
            uploads.pop(dataset_key, None)
            st.session_state[version_key] = upload_version + 1
            st.rerun()
        except Exception:
            st.error("ERA5 preparation did not finish. Check API availability and quotas, the geospatial dependencies and shapefile components. Completed downloads are retained; retry to resume.")
    st.caption("For Streamlit Cloud, publishing the small regional-average CSV from your completed notebook is faster and more reliable than running the full download in a web session. See README for the exact path.")

try:
    weather, source = load_weather(region_id, year, st.session_state.get("weather_uploads", {}).get(dataset_key))
except FileNotFoundError:
    st.info(f"No ERA5 data loaded for {region_id}, {year}. Open ‘Load weather data’ to upload the matching notebook export or fetch it through the API.")
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
        st.dataframe(outliers, use_container_width=True)
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
        st.dataframe(anomalies, use_container_width=True)
        st.download_button("Download temperature anomalies", anomalies.to_csv().encode(), f"{dataset_key}_lof_anomalies.csv", "text/csv")
