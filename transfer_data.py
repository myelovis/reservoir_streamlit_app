"""Fetch NO2–DK1 physical flows directly from the ENTSO-E API."""
from xml.etree import ElementTree

import numpy as np
import pandas as pd
import streamlit as st

from api_data import ApiDataError, get_response
from settings import get_secret
from transfer_plots import clip_intervals

URL = "https://web-api.tp.entsoe.eu/api"
NO2 = "10YNO-2--------T"
DK1 = "10YDK-1--------W"


def flow_records(payload, direction):
    try:
        root = ElementTree.fromstring(payload)
        for node in root.iter():
            node.tag = node.tag.rsplit("}", 1)[-1]
        if root.find("Reason") is not None:
            if root.findtext("Reason/code") == "999" and "no matching data" in (root.findtext("Reason/text") or "").lower():
                return []
            raise ApiDataError("ENTSO-E rejected the request. Check the token and selected year.")
        rows = []
        for series in root.findall("TimeSeries"):
            curve = series.findtext("curveType", "A01")
            if curve not in ("A01", "A03"):
                raise ValueError("Unsupported flow curve")
            for period in series.findall("Period"):
                start = pd.to_datetime(period.findtext("timeInterval/start"), utc=True)
                end = pd.to_datetime(period.findtext("timeInterval/end"), utc=True)
                step = pd.Timedelta(period.findtext("resolution"))
                if pd.isna(start) or pd.isna(end) or pd.isna(step) or step <= pd.Timedelta(0) or end <= start:
                    raise ValueError("Invalid flow period")
                points = sorted((int(p.findtext("position")), float(p.findtext("quantity")))
                                for p in period.findall("Point"))
                for index, (position, power) in enumerate(points):
                    when = start + (position - 1) * step
                    until = min(when + step, end)
                    if curve == "A03":
                        until = start + (points[index+1][0] - 1) * step if index+1 < len(points) else end
                    if position < 1 or not when < until <= end or not np.isfinite(power) or power < 0:
                        raise ValueError("Invalid flow point")
                    rows.append({"connection": "NO2-DK1", "direction": direction, "time": when,
                                 "power_mw": power, "hours": (until-when).total_seconds()/3600})
        if not rows and root.tag != "Publication_MarketDocument":
            raise ValueError("Unexpected flow response")
        return rows
    except (ElementTree.ParseError, ValueError, TypeError, OverflowError):
        raise ApiDataError("ENTSO-E returned invalid physical flow records. Try again later.") from None


@st.cache_data(ttl=3600, max_entries=12, show_spinner="Downloading physical flows from ENTSO-E…")
def load_transfers(year):
    token = get_secret("ENTSOE_TOKEN")
    start = pd.Timestamp(year=year, month=1, day=1, tz="Europe/Oslo")
    end = min(start + pd.DateOffset(years=1), pd.Timestamp.now(tz="Europe/Oslo").normalize())
    frames = []
    for direction, origin, destination in (("in", DK1, NO2), ("out", NO2, DK1)):
        response = get_response("ENTSO-E", URL, {
            "securityToken": token,
            "documentType": "A11",
            "out_Domain": origin,
            "in_Domain": destination,
            "periodStart": start.tz_convert("UTC").strftime("%Y%m%d%H%M"),
            "periodEnd": end.tz_convert("UTC").strftime("%Y%m%d%H%M"),
        })
        rows = flow_records(response.content, direction)
        if not rows:
            continue
        frame = pd.DataFrame(rows).drop_duplicates().sort_values("time")
        finish = (frame.time + pd.to_timedelta(frame.hours, unit="h")).cummax()
        if (frame.time.iloc[1:].to_numpy() < finish.iloc[:-1].to_numpy()).any():
            raise ApiDataError("ENTSO-E returned overlapping physical flow intervals.")
        frames.append(clip_intervals(frame, start, end))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).sort_values(["time", "direction"]).reset_index(drop=True)
