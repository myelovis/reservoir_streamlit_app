"""Shared Atlas reservoir loader and small plotting helpers."""
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from pymongo.errors import PyMongoError
from atlas_data import atlas_db, AtlasSetupError, DatasetNotReady

METRICS = {
    "fill_ratio": "Filling (fraction)",
    "capacity_twh": "Capacity (TWh)",
    "storage_twh": "Stored energy (TWh)",
    "fill_ratio_previous_week": "Previous filling (fraction)",
    "fill_ratio_change": "Weekly filling change (fraction difference)",
}

def prepare_reservoirs(records):
    names = {"dato_Id":"date_id", "omrType":"area_type", "omrnr":"area_number",
        "iso_aar":"iso_year", "iso_uke":"iso_week", "fyllingsgrad":"fill_ratio",
        "kapasitet_TWh":"capacity_twh", "fylling_TWh":"storage_twh",
        "neste_Publiseringsdato":"next_publication_date",
        "fyllingsgrad_forrige_uke":"fill_ratio_previous_week",
        "endring_fyllingsgrad":"fill_ratio_change"}
    df = pd.DataFrame(records).rename(columns=names)
    if not {"date_id", "area_type", "area_number", *METRICS}.issubset(df.columns):
        raise ValueError("Atlas reservoir records are missing required NVE fields.")
    df["date_id"] = pd.to_datetime(df["date_id"])
    if df.date_id.isna().any():
        raise ValueError("Atlas reservoir observations have missing dates.")
    for name in METRICS:
        df[name] = pd.to_numeric(df[name], errors="raise")
    if not np.isfinite(df[list(METRICS)].to_numpy()).all():
        raise ValueError("Atlas reservoir measurements must be finite.")
    if df.duplicated(["area_type", "area_number", "date_id"]).any():
        raise ValueError("Duplicate reservoir observations in Atlas.")
    if "next_publication_date" in df:
        df["next_publication_date"] = pd.to_datetime(df["next_publication_date"], format="ISO8601", errors="coerce")
    df = df.drop(columns=["publication_id"], errors="ignore")
    return df.sort_values(["area_type", "area_number", "date_id"])


@st.cache_data(ttl=300, show_spinner="Reading reservoir observations from Atlas…")
def load_reservoirs():
    db = atlas_db()
    meta = db["reservoir_datasets"].find_one({"_id": "current"})
    if not meta or meta.get("status") != "complete" or not meta.get("publication_id"):
        raise DatasetNotReady("Publish NVE reservoir data to Atlas once: python publish_atlas.py --reservoirs")
    records = list(db["reservoir_weekly"].find({"publication_id": meta["publication_id"]}, {"_id": 0}))
    after = db["reservoir_datasets"].find_one({"_id": "current"})
    if not after or after.get("status") != "complete" or after.get("publication_id") != meta["publication_id"]:
        raise DatasetNotReady("Reservoir data is being updated. Refresh after publication finishes.")
    if len(records) != meta.get("rows"):
        raise ValueError("Atlas reservoir dataset is incomplete; republish it from NVE.")
    return prepare_reservoirs(records)

def _remember_area():
    st.session_state["selected_area_type"] = st.session_state["_area_type"]
    st.session_state.pop("selected_area_number", None)


def _remember_number():
    st.session_state["selected_area_number"] = st.session_state["_area_number"]


def choose_area(default_kind="NO", default_number=0):
    try:
        df = load_reservoirs()
    except (AtlasSetupError, DatasetNotReady) as error:
        st.info(str(error))
        st.stop()
    except PyMongoError:
        st.error("Atlas could not be read. Check MONGO_URI, database-user permissions and Atlas Network Access.")
        st.stop()
    except (ValueError, KeyError):
        st.error("Atlas reservoir records could not be validated. Republish the NVE dataset.")
        st.stop()
    available = df.area_type.unique() if not df.empty else []
    kinds = [kind for kind in ["NO", "EL", "VASS"] if kind in available]
    if not kinds:
        st.info("No reservoir areas are available in the published Atlas dataset.")
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
    st.caption("Plot source: MongoDB Atlas · nve.reservoir_weekly · originally published from NVE.")
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
