"""Read region-specific ERA5 exports from the notebook or prepare them on demand."""
from pathlib import Path
from io import BytesIO
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
VARIABLES = ["temperature_2m", "precipitation"]


def validate_weather(frame, region_id, year):
    if region_id not in {f"NO{i}" for i in range(1, 6)}:
        raise ValueError("This ERA5 pipeline uses electricity areas NO1–NO5 only.")
    frame = frame.copy()
    if "time" not in frame.columns:
        raise ValueError("CSV must contain time, temperature_2m and precipitation columns.")
    for name in VARIABLES:
        if name not in frame:
            raise ValueError(f"Missing weather column: {name}.")
        frame[name] = pd.to_numeric(frame[name], errors="raise")
    if "region_id" in frame and not frame.region_id.eq(region_id).all():
        raise ValueError("The uploaded region does not match the selected electricity area.")
    frame["time"] = pd.to_datetime(frame["time"], utc=True, errors="raise")
    frame = frame.set_index("time").sort_index()
    expected = pd.date_range(f"{year}-01-01", f"{year+1}-01-01", freq="h", inclusive="left", tz="UTC")
    if not frame.index.equals(expected):
        raise ValueError(f"Expected all {len(expected):,} unique consecutive UTC hours of {year}; do not upload a partial year or a single grid-cell file.")
    if not np.isfinite(frame[VARIABLES].to_numpy()).all() or frame.precipitation.lt(0).any():
        raise ValueError("Weather values must be finite and precipitation cannot be negative.")
    return frame[VARIABLES]


def load_weather(region_id, year, uploaded=None, root=ROOT):
    if uploaded is not None:
        return validate_weather(pd.read_csv(BytesIO(uploaded)), region_id, year), "Uploaded ERA5 regional averages"
    candidates = [
        Path(root) / "data" / "weather" / f"{region_id}_{year}.csv",
        Path(root) / "weather_fast" / f"{region_id}_{year}-01-01_{year}-12-31_1000pts" / "regional_hourly_mean.csv",
    ]
    for path in candidates:
        if path.is_file():
            return validate_weather(pd.read_csv(path), region_id, year), f"Saved ERA5 export: {path.name}"
    raise FileNotFoundError(f"No saved ERA5 regional averages for {region_id}, {year}.")


def prepare_weather(region_id, year):
    # Optional geospatial imports are only needed when preparing new API data.
    from era5_module import ingest_region
    points, weather = ingest_region(region_id, (f"{year}-01-01", f"{year}-12-31"),
                                    n=1000, output=str(ROOT / "weather_fast"))
    if len(points) != 1000:
        raise ValueError("Expected 1,000 sample locations.")
    exported = validate_weather(weather.rename_axis("time").reset_index(), region_id, year)
    target = ROOT / "data" / "weather" / f"{region_id}_{year}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    exported.assign(region_id=region_id).to_csv(temporary, index=True)
    temporary.replace(target)
    return exported
