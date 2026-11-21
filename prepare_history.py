"""Reuse saved locations for 1995–2023. Stop and resume without losing work."""
import argparse
import hashlib
import json
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import requests
from requests.adapters import HTTPAdapter
from region_tools import DATA, read_areas, samples_hash
from local_store import read_samples
from restore_samples import check_samples
from prepare_all_weather import api_request, locate_cells
from history_store import year_dates, encode, decode, publish_year

CACHE = DATA/'weather_cache'
FOLDER = DATA/'history25_v1'


def show_response(response, *args, **kwargs):
    print(f'API response: HTTP {response.status_code}.', flush=True)
    wait = response.headers.get('Retry-After')
    if wait:
        print(f'Server Retry-After: {wait}. Wait before starting another run.', flush=True)
    return response


def make_plan(points, areas):
    """Pick existing points once; use the same selection in every year."""
    locations = gpd.GeoSeries(gpd.points_from_xy(points.longitude, points.latitude), crs=4326, index=points.index)
    groups = {}
    for area in areas.sort_values('area_id').itertuples():
        pool = points.loc[locations.covered_by(area.geometry)].sort_values('point_id')
        if area.area_id.startswith('NO') and area.area_id != 'NO0':
            pool = pool.loc[pool.region_id.eq(area.area_id)]
        if len(pool) < 25:
            raise ValueError(f'{area.area_id} has fewer than 25 original points. No new points were created.')
        if area.area_id != 'NO0':
            if area.area_id.startswith('VASS'):
                # Prefer the price-area subset so we can reuse its downloads.
                price_ids = {point for region, info in groups.items() if region.startswith('NO')
                             for point in info['point_ids']}
                shared = pool.loc[pool.point_id.isin(price_ids)]
                if len(shared) >= 25:
                    pool = shared
            status = getattr(area, 'boundary_status', 'unverified')
            groups[area.area_id] = dict(point_ids=sorted(pool.sample(n=25, random_state=42).point_id),
                boundary_hash=hashlib.sha256(area.geometry.wkb).hexdigest(),
                boundary_status=str(status) if pd.notna(status) else 'unverified')
    national = areas.loc[areas.area_id.eq('NO0')].iloc[0]
    groups['NO0'] = dict(point_ids=sorted({point for region, info in groups.items()
        if region.startswith('NO') for point in info['point_ids']}),
        boundary_hash=hashlib.sha256(national.geometry.wkb).hexdigest(), boundary_status='price-area union')
    plan = dict(source_samples_hash=samples_hash(points), regions=groups)
    plan['plan_hash'] = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    return plan


def save_plan(plan):
    FOLDER.mkdir(parents=True, exist_ok=True)
    path = FOLDER/'manifest.json'
    if path.exists() and json.loads(path.read_text()) != plan:
        raise ValueError('The saved history plan uses different points or boundaries. It was not replaced.')
    if not path.exists():
        path.write_text(json.dumps(plan, indent=2), encoding='utf-8')


def grid_points(source, plan, session, year):
    ids = {point for info in plan['regions'].values() for point in info['point_ids']}
    selected = source.loc[source.point_id.isin(ids)].copy()
    columns = ['grid_id', 'grid_latitude', 'grid_longitude']
    if not set(columns).issubset(selected.columns) or selected[columns].isna().any().any():
        path = CACHE/f"grid_points_{plan['source_samples_hash'][:12]}.csv"
        if path.exists():
            cached = pd.read_csv(path, dtype={'grid_id': str}).set_index('point_id')
            matched = cached.reindex(selected.point_id)
            if not np.allclose(matched[['latitude', 'longitude']], selected[['latitude', 'longitude']], rtol=0, atol=1e-10):
                raise ValueError('The cached grid map does not match the original points.')
            for column in columns:
                selected[column] = matched[column].to_numpy()
    if not set(columns).issubset(selected.columns) or selected[columns].isna().any().any():
        selected = locate_cells(selected, year, samples_hash(selected), session)
    return selected


def download_year(points, year, session, remaining, pause):
    cells = points.drop_duplicates('grid_id').copy()
    cells['latitude'], cells['longitude'] = cells.grid_latitude, cells.grid_longitude
    missing = []
    print(f'{year}: checking {len(cells)} cached grid cells…', flush=True)
    for row in cells.itertuples():
        path = CACHE/f'{year}_{row.grid_id}.npz'
        if path.exists():
            decode(path.read_bytes(), year)
        else:
            missing.append(row.grid_id)
    needed = cells.loc[cells.grid_id.isin(missing)]
    count = min(len(needed), remaining)
    print(f'{year}: {len(cells)-len(needed)} cached; {len(needed)} missing.', flush=True)
    for start in range(0, count, 5):
        batch = needed.iloc[start:min(start+5, count)]
        print(f'{year}: requesting cells {start+1}–{min(start+5, count)} of {len(needed)} missing cells…', flush=True)
        payload = api_request(session, batch, f'{year}-01-01', f'{year}-12-31')
        for point, item in zip(batch.itertuples(), payload):
            dates = pd.DatetimeIndex(pd.to_datetime(item['hourly']['time'], utc=True))
            if not dates.equals(year_dates(year)):
                raise ValueError('The API returned incomplete hours. The cell was not saved.')
            returned = f"{item['latitude']:.6f}_{item['longitude']:.6f}"
            if returned != point.grid_id:
                raise ValueError('The API returned a different grid cell. Check the saved grid map.')
            values = np.column_stack([item['hourly'][name] for name in ['temperature_2m', 'precipitation']])
            path = CACHE/f'{year}_{point.grid_id}.npz'
            temporary = path.with_suffix('.tmp')
            temporary.write_bytes(encode(values, year))
            temporary.replace(path)
        print(f'{year}: cached {min(start+5, count)}/{len(needed)} missing cells.', flush=True)
        print(f'Waiting {pause:g} seconds between batches…', flush=True)
        time.sleep(pause)
    return count, count == len(needed)


def aggregate_year(points, plan, year):
    print(f'{year}: calculating regional averages…', flush=True)
    weights = {}
    for region, info in plan['regions'].items():
        chosen = points.loc[points.point_id.isin(info['point_ids'])]
        grouped = chosen.groupby('grid_id').area_weight.sum()
        weights[region] = grouped/grouped.sum()
    arrays = {region: np.zeros((len(year_dates(year)), 2)) for region in weights}
    for cell in points.grid_id.unique():
        values = decode((CACHE/f'{year}_{cell}.npz').read_bytes(), year).to_numpy()
        for region, shares in weights.items():
            if cell in shares:
                arrays[region] += values*shares[cell]
    for region, values in arrays.items():
        path = FOLDER/f'{year}_{region}.npz'
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(encode(values, year))
        temporary.replace(path)
    print(f'{year}: saved {len(arrays)} regional hourly averages locally.', flush=True)


def main(args):
    if not 1940 <= args.start <= args.end < pd.Timestamp.now(tz='Europe/Paris').year:
        raise ValueError('Choose complete historical years in order.')
    points = check_samples(read_samples())
    areas = pd.concat([read_areas(kind) for kind in ['EL', 'NO', 'VASS']], ignore_index=True)
    expected = {'NO0', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'VASS1', 'VASS2', 'VASS3'}
    if set(areas.area_id) != expected:
        raise ValueError('Add all five price areas, national NO0, and VASS1–VASS3 boundaries first.')
    plan = make_plan(points, areas)
    ids = {point for info in plan['regions'].values() for point in info['point_ids']}
    print(f'25 existing points per price/VASS area; NO0 uses 125 price-area points. {len(ids)} unique locations in total.')
    print(f'Years {args.start}–{args.end}. Original samples and old Atlas collections are not replaced.')
    if args.plan:
        print('Plan only. No downloads or database writes. Some locations share an ERA5 grid cell.')
        return
    save_plan(plan)
    if args.publish:
        from pymongo import MongoClient
        from settings import get_secret
        with MongoClient(get_secret('MONGO_URI'), tz_aware=True, serverSelectionTimeoutMS=15000) as client:
            client.admin.command('ping')
            original = check_samples(pd.DataFrame(list(client['nve'].era5_samples_v4.find({}, {'_id': 0}))))
            if samples_hash(original) != plan['source_samples_hash']:
                raise ValueError('Local points differ from the original Atlas points. Run restore_samples.py first.')
            for year in range(args.start, args.end+1):
                publish_year(client['nve'], FOLDER, plan, year)
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    remaining = args.max_cells
    with requests.Session() as session:
        # Return server errors immediately instead of waiting silently to retry.
        session.mount('https://', HTTPAdapter(max_retries=0))
        session.hooks['response'].append(show_response)
        located = None
        for year in range(args.start, args.end+1):
            if all((FOLDER/f'{year}_{region}.npz').exists() for region in plan['regions']):
                for region in plan['regions']:
                    decode((FOLDER/f'{year}_{region}.npz').read_bytes(), year)
                print(f'{year}: regional files already complete; skipped.', flush=True)
                continue
            if located is None:
                located = grid_points(points, plan, session, year)
            used, complete = download_year(located, year, session, remaining, args.pause)
            remaining -= used
            if not complete:
                print('Download budget reached. Run the same command again to resume. Publish only finished years.')
                return
            aggregate_year(located, plan, year)
    print('Selected years are ready locally. Add --publish to upload compressed regional averages.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', type=int, default=1995)
    parser.add_argument('--end', type=int, default=2023)
    parser.add_argument('--max-cells', type=int, default=100, help='Maximum new annual grid-cell downloads per run')
    parser.add_argument('--pause', type=float, default=15, help='Seconds between batches of up to five annual cells')
    parser.add_argument('--plan', action='store_true', help='Check saved points and boundaries without downloading')
    parser.add_argument('--publish', action='store_true', help='Publish local history only; no API download')
    args = parser.parse_args()
    if args.max_cells < 1 or args.pause < 15:
        parser.error('Use at least one cell and at least 15 seconds between batches.')
    try:
        main(args)
    except KeyboardInterrupt:
        raise SystemExit('\nStopped. Saved cache files are safe. Run the same command to resume.') from None
    except requests.RequestException:
        raise SystemExit('The weather API could not be reached. Cached cells are safe; resume later.') from None
    except Exception as error:
        from pymongo.errors import PyMongoError
        if isinstance(error, PyMongoError):
            raise SystemExit('Atlas could not be reached. Check your saved connection and Atlas Network Access.') from None
        if isinstance(error, (ValueError, RuntimeError, FileNotFoundError)):
            raise SystemExit(str(error)) from None
        raise

