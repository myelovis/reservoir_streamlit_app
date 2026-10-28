"""Shared NVE loader and small plotting helpers."""
import pandas as pd
import requests
import streamlit as st
import matplotlib.pyplot as plt

METRICS = {
    "fill_ratio": "Filling (fraction)",
    "capacity_twh": "Capacity (TWh)",
    "storage_twh": "Stored energy (TWh)",
    "fill_ratio_previous_week": "Previous filling (fraction)",
    "fill_ratio_change": "Weekly filling change (fraction difference)",
}

@st.cache_data(ttl=3600)
def load_reservoirs():
    url = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    names = {"dato_Id":"date_id", "omrType":"area_type", "omrnr":"area_number",
        "iso_aar":"iso_year", "iso_uke":"iso_week", "fyllingsgrad":"fill_ratio",
        "kapasitet_TWh":"capacity_twh", "fylling_TWh":"storage_twh",
        "neste_Publiseringsdato":"next_publication_date",
        "fyllingsgrad_forrige_uke":"fill_ratio_previous_week",
        "endring_fyllingsgrad":"fill_ratio_change"}
    df = pd.DataFrame(response.json()).rename(columns=names)
    df["date_id"] = pd.to_datetime(df["date_id"])
    df["next_publication_date"] = pd.to_datetime(
        df["next_publication_date"], format="ISO8601", errors="coerce")
    return df.sort_values(["area_type", "area_number", "date_id"])

def _remember_area():
    st.session_state["selected_area_type"] = st.session_state["_area_type"]
    st.session_state.pop("selected_area_number", None)


def _remember_number():
    st.session_state["selected_area_number"] = st.session_state["_area_number"]


def choose_area(default_kind="NO", default_number=0):
    try:
        df = load_reservoirs()
    except (requests.RequestException, ValueError, KeyError):
        st.error("NVE data could not be read. Refresh after checking the API connection.")
        st.stop()
    available = df.area_type.unique() if not df.empty else []
    kinds = [kind for kind in ["NO", "EL", "VASS"] if kind in available]
    if not kinds:
        st.info("No reservoir areas are available from NVE.")
        st.stop()
    # Permanent keys survive Streamlit's cleanup of widgets on other pages.
    saved_kind = st.session_state.get("selected_area_type", default_kind)
    st.session_state["_area_type"] = saved_kind if saved_kind in kinds else kinds[0]
    kind = st.sidebar.radio("Area type", kinds, key="_area_type", on_change=_remember_area)
    st.session_state["selected_area_type"] = kind
    numbers = sorted(df.loc[df.area_type.eq(kind), "area_number"].unique())
    saved_number = st.session_state.get("selected_area_number", default_number)
    st.session_state["_area_number"] = saved_number if saved_number in numbers else numbers[0]
    number = st.sidebar.selectbox("Area number", numbers, key="_area_number", on_change=_remember_number)
    st.session_state["selected_area_number"] = number
    st.caption("NO: national; EL: price area; VASS: watercourse area. These classifications overlap.")
    return df.loc[df.area_type.eq(kind) & df.area_number.eq(number)].sort_values("date_id").set_index("date_id")

def reservoir_plot(series, column):
    if column == "All measures":
        values = series[list(METRICS)]
        spread = (values.max() - values.min()).replace(0, 1)
        values = (values - values.min()) / spread
        ylabel = "Min–max scaled value (0–1)"
    else:
        values = series[[column]]
        ylabel = METRICS[column]
    fig, ax = plt.subplots(figsize=(10, 4))
    values.rename(columns=METRICS).plot(ax=ax, marker="o", markersize=3)
    area = f"{series.area_type.iloc[0]}{series.area_number.iloc[0]}"
    ax.set(title=f"{area}: reservoir observations", xlabel="Observation date", ylabel=ylabel)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig
