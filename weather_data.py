"""Fetch and cache regional hourly ERA5 observations directly from Open-Meteo."""
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from api_data import ApiDataError, get_json
from region_tools import read_areas, sample_regions
from ui_feedback import fetch_progress

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
FIRST_DAY = date(1940, 1, 1)
PROPERTIES = ("temperature_2m", "precipitation")
SAMPLE_COUNT = 5


def archive_end():
    # Use a full UTC date and allow for the published ERA5 update delay.
    return pd.Timestamp.now(tz="UTC").date() - timedelta(days=6)


def weather_years(region_id):
    """Return complete calendar years in the archive's advertised range."""
    end = archive_end()
    last = end.year if (end.month, end.day) == (12, 31) else end.year - 1
    return range(FIRST_DAY.year, last + 1)


@st.cache_data(show_spinner=False)
def sample_coordinates(region_id):
    kind = "VASS" if region_id.startswith("VASS") else "NO" if region_id == "NO0" else "EL"
    areas = read_areas(kind)
    area = areas.loc[areas.area_id.eq(region_id)]
    if area.empty:
        raise ApiDataError(f"No boundary is available for {region_id}.")
    points = sample_regions(area, n=SAMPLE_COUNT)
    note = " · approximate boundary" if area.iloc[0].get("boundary_status") == "approximate" else ""
    return points[["latitude", "longitude"]], note


@st.cache_data(ttl=86400, max_entries=64, show_spinner=False)
def fetch_period(region_id, start, end):
    points, note = sample_coordinates(region_id)
    payload = get_json("Open-Meteo ERA5", ARCHIVE, {
        "latitude": ",".join(points.latitude.map(lambda value: f"{value:.5f}")),
        "longitude": ",".join(points.longitude.map(lambda value: f"{value:.5f}")),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": ",".join(PROPERTIES),
        "models": "era5",
        "timezone": "GMT",
    })
    expected = pd.date_range(start, end + timedelta(days=1), inclusive="left", freq="h", tz="UTC")
    if not isinstance(payload, list) or len(payload) != len(points):
        raise ApiDataError(f"Open-Meteo did not return all weather samples for {region_id}. Retry or shorten the range.")
    frames = []
    try:
        for location in payload:
            hourly = pd.DataFrame(location["hourly"])
            index = pd.DatetimeIndex(pd.to_datetime(hourly["time"], utc=True))
            values = hourly[list(PROPERTIES)].apply(pd.to_numeric).to_numpy(dtype=float)
            if not index.equals(expected) or not np.isfinite(values).all() or (values[:, 1] < 0).any():
                raise ValueError("Incomplete or invalid hourly series")
            frames.append(values)
    except (KeyError, TypeError, ValueError):
        raise ApiDataError(f"Open-Meteo returned missing or invalid hours for {region_id}. Change the dates or retry.") from None
    expected.name = "time"
    frame = pd.DataFrame(np.mean(frames, axis=0), index=expected, columns=PROPERTIES)
    return frame, f"Open-Meteo ERA5 API · {region_id} · mean of {len(points)} fixed sample points{note}"


def load_period(region_id, start, end, update=None):
    start, end = pd.Timestamp(start).date(), pd.Timestamp(end).date()
    available = archive_end()
    if start < FIRST_DAY or start > end or end > available:
        raise ApiDataError(f"Choose ERA5 dates between {FIRST_DAY} and {available}. Recent days have a publication delay.")
    if update is None:
        with fetch_progress("Open-Meteo weather") as report:
            return load_period(region_id, start, end, update=report)
    parts = []
    years = range(start.year, end.year + 1)
    for index, year in enumerate(years):
        update(round(100 * index / len(years)), f"Requesting or reading {region_id} · {year}")

        frame, source = fetch_period(
            region_id, max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
        )
        parts.append(frame)
        update(round(95 * (index + 1) / len(years)), f"Weather validated · {region_id} · {year}")
    return pd.concat(parts), source


def load_weather(region_id, year):
    return load_period(region_id, date(year, 1, 1), date(year, 12, 31))
