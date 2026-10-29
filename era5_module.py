"""Install: pip install geopandas numpy pandas requests"""
from pathlib import Path
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SHAPEFILE = Path(__file__).resolve().parent / "electricity_NO1_NO5.shp"
VARIABLES = "temperature_2m,precipitation"
URL = "https://archive-api.open-meteo.com/v1/archive"

session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5, backoff_factor=5, status_forcelist=[429, 500, 502, 503, 504],
)))


def sample_points(region_id, n=1000):
    if SHAPEFILE.is_file():
        regions = gpd.read_file(SHAPEFILE)
    else:
        # On a clean deployment, obtain the same official electricity polygons
        # directly; never substitute administrative or watershed regions.
        response = session.get(
            "https://kart.nve.no/enterprise/rest/services/Nettomraader/MapServer/0/query",
            params={"where": "1=1", "outFields": "budomr", "returnGeometry": "true",
                    "outSR": 25833, "f": "geojson"}, timeout=120)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload or payload.get("exceededTransferLimit"):
            raise ValueError("NVE electricity boundaries could not be read completely.")
        regions = gpd.GeoDataFrame.from_features(payload["features"], crs=25833)
        regions["region"] = regions["budomr"].str.replace(" ", "", regex=False)
        if set(regions.region) != {f"NO{i}" for i in range(1, 6)}:
            raise ValueError("Expected NVE electricity areas NO1–NO5.")
    selected = regions.loc[regions["region"] == region_id]
    if selected.empty:
        raise ValueError(f"Unknown region: {region_id}")
    polygon = selected.to_crs(3035).geometry.union_all()
    xmin, ymin, xmax, ymax = polygon.bounds
    rng, points = np.random.default_rng(42), []
    while len(points) < n:
        x, y = rng.uniform([xmin, ymin], [xmax, ymax], (2000, 2)).T
        candidates = gpd.GeoSeries(gpd.points_from_xy(x, y), crs=3035)
        points.extend(candidates[candidates.within(polygon)].tolist())
    points = gpd.GeoSeries(points[:n], crs=3035).to_crs(4326)
    return pd.DataFrame({
        "point_id": range(n), "latitude": points.y, "longitude": points.x,
    })


def request_batch(points, start, end):
    response = session.get(URL, params={
        "latitude": ",".join(points.latitude.astype(str)),
        "longitude": ",".join(points.longitude.astype(str)),
        "start_date": start, "end_date": end,
        "hourly": VARIABLES, "models": "era5", "timezone": "GMT",
        "cell_selection": "nearest", "elevation": ",".join(["nan"] * len(points)),
    }, timeout=180)
    response.raise_for_status()
    data = response.json()
    data = data if isinstance(data, list) else [data]
    if len(data) != len(points) or any("hourly" not in d for d in data):
        raise ValueError("Unexpected API response")
    return data


def ingest_region(region_id, time_interval, n=1000, output="weather_fast"):
    start, end = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in time_interval]
    if start > end:
        raise ValueError("Start must precede end")
    folder = Path(output) / f"{region_id}_{start}_{end}_{n}pts"
    folder.mkdir(parents=True, exist_ok=True)
    sample_file = folder / "samples.csv"
    if not sample_file.exists():
        sample_points(region_id, n).to_csv(sample_file, index=False)
    points = pd.read_csv(sample_file)

    # Ask the API which ERA5 cell each point uses; retain cached probes.
    probes = []
    for i in range(0, n, 50):
        cache = folder / f"grid_map_{i:04d}.csv"
        batch = points.iloc[i:i + 50]
        if not cache.exists():
            data = request_batch(batch, start, start)
            batch = batch.assign(grid_lat=[d["latitude"] for d in data],
                                 grid_lon=[d["longitude"] for d in data])
            batch.to_csv(cache, index=False)
            time.sleep(2)
        probes.append(pd.read_csv(cache))
    points = pd.concat(probes, ignore_index=True)
    points["grid_id"] = points.groupby(["grid_lat", "grid_lon"], sort=True).ngroup()
    points.to_csv(sample_file, index=False)
    cells = points.drop_duplicates("grid_id")
    pending = cells[~cells.grid_id.map(lambda g: (folder / f"cell_{g:04d}.csv.gz").exists())]
    expected = pd.date_range(start, pd.Timestamp(end) + pd.Timedelta(days=1),
                             freq="h", inclusive="left", tz="UTC")
    print(f"{n} sample points use {len(cells)} ERA5 cells.", flush=True)

    # Fetch one representative sample per cell, five locations per request.
    for i in range(0, len(pending), 5):
        batch = pending.iloc[i:i + 5]
        for point, result in zip(batch.itertuples(index=False), request_batch(batch, start, end)):
            frame = pd.DataFrame(result["hourly"])
            frame["time"] = pd.to_datetime(frame["time"], utc=True)
            if not pd.DatetimeIndex(frame.time).equals(expected):
                raise ValueError("Incomplete hourly timestamps")
            if frame[VARIABLES.split(",")].isna().any().any():
                raise ValueError("Missing weather values")
            if (result["latitude"], result["longitude"]) != (point.grid_lat, point.grid_lon):
                raise ValueError("API selected a different grid cell")
            target = folder / f"cell_{point.grid_id:04d}.csv.gz"
            temporary = target.with_suffix(".tmp")
            frame.assign(grid_id=point.grid_id).to_csv(temporary, index=False, compression="gzip")
            temporary.replace(target)
        print(f"Saved {min(i + 5, len(pending))}/{len(pending)} pending cells", flush=True)
        time.sleep(2)

    # Weight each cell by its number of sampled points, preserving sample means.
    weights = points.grid_id.value_counts()
    mean = None
    for grid_id, count in weights.items():
        frame = pd.read_csv(folder / f"cell_{grid_id:04d}.csv.gz", parse_dates=["time"])
        weighted = frame.set_index("time")[VARIABLES.split(",")] * (count / n)
        mean = weighted if mean is None else mean + weighted
    mean.to_csv(folder / "regional_hourly_mean.csv")
    return points, mean


if __name__ == "__main__":
    ingest_region("NO3", ("2024-01-01", "2024-12-31"))

