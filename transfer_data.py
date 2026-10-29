"""Read the notebook's Spark-extracted records from MongoDB."""
import pandas as pd
import numpy as np
import streamlit as st
from pymongo import MongoClient
from transfer_plots import clip_intervals

@st.cache_data(ttl=300)
def load_transfers():
    end = pd.Timestamp.now(tz="Europe/Oslo").normalize()
    start = end - pd.DateOffset(years=2)
    with MongoClient(st.secrets["MONGO_URI"], tz_aware=True,
                     serverSelectionTimeoutMS=10000) as client:
        records = list(client["nve"]["simple_transfers"].find({
            "connection": "NO2-DK1",
            "direction": {"$in": ["in", "out"]},
            # The notebook clips API blocks at monthly request boundaries.
            "time": {"$gte": start.replace(day=1).to_pydatetime(), "$lt": end.to_pydatetime()},
        }, {"_id": 0}))
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values(["time", "direction"]).reset_index(drop=True)
    values = df[["power_mw", "hours", "energy_mwh"]].apply(pd.to_numeric)
    if (df.time.isna().any() or not np.isfinite(values).all().all()
        or (values.hours <= 0).any() or (values.power_mw < 0).any()
        or not np.allclose(values.energy_mwh, values.power_mw*values.hours)):
        raise ValueError("Invalid durations, power or energy in the published records.")
    df[values.columns] = values
    for _, group in df.groupby(["connection", "direction"]):
        finish = (group.time + pd.to_timedelta(group.hours, unit="h")).cummax()
        if (group.time.iloc[1:].to_numpy() < finish.iloc[:-1].to_numpy()).any():
            raise ValueError("Overlapping intervals in the published records.")
    return clip_intervals(df, start, end).sort_values(["time", "direction"]).reset_index(drop=True)
