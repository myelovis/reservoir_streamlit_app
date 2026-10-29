"""Read full-year ERA5 regional averages from Atlas, never local CSVs."""
import numpy as np
import pandas as pd
import streamlit as st
from atlas_data import atlas_db, DatasetNotReady

VARIABLES = ["temperature_2m", "precipitation"]


def validate_weather(frame, region_id, year):
    if region_id not in {f"NO{i}" for i in range(1, 6)}:
        raise ValueError("This ERA5 pipeline uses electricity areas NO1–NO5 only.")
    frame = frame.copy()
    if not {"time", *VARIABLES}.issubset(frame.columns):
        raise ValueError("Atlas weather records must contain time, temperature_2m and precipitation.")
    for name in VARIABLES:
        frame[name] = pd.to_numeric(frame[name], errors="raise")
    if "region_id" in frame and not frame.region_id.eq(region_id).all():
        raise ValueError("Atlas records do not match the selected electricity region.")
    if "model" in frame and not frame.model.eq("era5").all():
        raise ValueError("Expected ERA5 reanalysis records only.")
    frame["time"] = pd.to_datetime(frame["time"], utc=True, errors="raise")
    frame = frame.set_index("time").sort_index()
    expected = pd.date_range(f"{year}-01-01", f"{year+1}-01-01", freq="h", inclusive="left", tz="UTC")
    if not frame.index.equals(expected):
        raise ValueError(f"Expected all {len(expected):,} unique consecutive UTC hours of {year} in Atlas.")
    if not np.isfinite(frame[VARIABLES].to_numpy()).all() or frame.precipitation.lt(0).any():
        raise ValueError("Weather values must be finite and precipitation cannot be negative.")
    return frame[VARIABLES]


@st.cache_data(ttl=300, show_spinner="Reading ERA5 regional averages from Atlas…")
def load_weather(region_id, year):
    if region_id not in {f"NO{i}" for i in range(1, 6)}:
        raise ValueError("Choose electricity area NO1–NO5.")
    db = atlas_db()
    dataset_id = f"era5_{region_id}_{year}"
    meta = db["era5_datasets"].find_one({"_id": dataset_id})
    if not meta or meta.get("status") != "complete":
        raise DatasetNotReady(f"Publish the completed {region_id}, {year} ERA5 dataset from Jupyter to Atlas first.")
    if meta.get("region_id") != region_id or meta.get("year") != year or meta.get("model") != "era5":
        raise ValueError("Atlas dataset metadata does not match the chosen region, year and ERA5 model.")
    sample_count = meta.get("source_sample_count", meta.get("sample_count"))
    if sample_count != 1000:
        raise ValueError("The ERA5 dataset must represent 1,000 sampled locations.")
    query = {"region_id": region_id, "model": "era5", "time": {
        "$gte": pd.Timestamp(f"{year}-01-01", tz="UTC").to_pydatetime(),
        "$lt": pd.Timestamp(f"{year+1}-01-01", tz="UTC").to_pydatetime()}}
    records = list(db["era5_hourly"].find(query, {"_id": 0}).sort("time", 1))
    after = db["era5_datasets"].find_one({"_id": dataset_id})
    if not after or after.get("status") != "complete" or after.get("updated_at") != meta.get("updated_at"):
        raise DatasetNotReady("The ERA5 dataset is being updated. Refresh after publication finishes.")
    weather = validate_weather(pd.DataFrame(records), region_id, year)
    if meta.get("hours") != len(weather):
        raise ValueError("Atlas weather row count does not match its publication metadata.")
    return weather, f"MongoDB Atlas · nve.era5_hourly · {region_id}, {year} · 1,000 sampled locations"
