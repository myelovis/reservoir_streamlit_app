"""Small tools for boundaries, clicks and random points."""
from pathlib import Path
import hashlib
import json
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

DATA = Path(__file__).resolve().parent / 'data'


def samples_hash(points):
    columns=['point_id','region_id','latitude','longitude','area_weight']
    text=points[columns].sort_values('point_id').to_csv(index=False,float_format='%.12g')
    return hashlib.sha256(text.encode()).hexdigest()


def read_areas(kind):
    path = DATA / f'{kind}.geojson'
    if not path.exists():
        raise ValueError(f'Add official {kind} boundaries first. See START_HERE.md, step 1.')
    payload = json.loads(path.read_text(encoding='utf-8'))
    areas = gpd.GeoDataFrame.from_features(payload['features'],crs=4326)
    needed = {'area_id', 'area_type', 'area_number', 'name'}
    if not needed.issubset(areas.columns) or areas.empty:
        raise ValueError('Boundary files need area_id, area_type, area_number and name.')
    if not areas.area_type.eq(kind).all() or areas.area_id.duplicated().any():
        raise ValueError('Boundary IDs must be unique and match the chosen area type.')
    if kind=='VASS' and set(areas.area_id)!={'VASS1','VASS2','VASS3'}:
        raise ValueError('Use the three published Magasinstatistikk water areas, VASS1 to VASS3. Do not use the four-area descriptive list as a boundary mapping.')
    if areas.geometry.is_empty.any() or not areas.geometry.is_valid.all():
        raise ValueError('A boundary is empty or invalid. Repair the source file first.')
    return areas


def clicked_area(areas, latitude, longitude):
    found = areas.loc[areas.geometry.covers(Point(longitude, latitude))]
    return None if found.empty else found.iloc[0]


def sample_regions(areas, n=200, seed=42):
    if n < 1:
        raise ValueError('Use at least one point per region.')
    rng, rows = np.random.default_rng(seed), []
    for area in areas.to_crs(3035).itertuples():
        polygon = area.geometry
        low_x, low_y, high_x, high_y = polygon.bounds
        points = []
        # Metres give each part of the region the same chance.
        for _ in range(10000):
            xy = rng.uniform([low_x, low_y], [high_x, high_y], (max(500, n), 2))
            points.extend(Point(x, y) for x, y in xy if polygon.contains(Point(x, y)))
            if len(points) >= n:
                break
        if len(points) < n:
            raise ValueError(f'Could not sample enough points in {area.area_id}.')
        coordinates = gpd.GeoSeries(points[:n], crs=3035).to_crs(4326)
        for number, point in enumerate(coordinates):
            rows.append({'point_id': f'{area.area_id}_{number}', 'region_id': area.area_id,
                         'latitude': point.y, 'longitude': point.x,
                         'area_weight': polygon.area / n})
    return pd.DataFrame(rows)


def area_weights(points, areas):
    locations = gpd.GeoDataFrame(points.copy(), geometry=gpd.points_from_xy(
        points.longitude, points.latitude), crs=4326)
    result = {}
    for area in areas.itertuples():
        chosen = locations.loc[locations.geometry.covered_by(area.geometry)]
        if chosen.empty:
            raise ValueError(f'No samples fall inside {area.area_id}. Add more points.')
        # Each price area has 200 points, but price areas have different sizes.
        result[area.area_id] = chosen.groupby('grid_id').area_weight.sum()
    return result
