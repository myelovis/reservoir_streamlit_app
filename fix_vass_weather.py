"""Build VASS weather from saved ERA5 cells; optionally publish only VASS."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from region_tools import DATA, read_areas, area_weights, samples_hash
from local_store import DATABASE, read_samples, save_samples, save_weather
from weather_data import validate_weather


def cached_points(cache):
    points = read_samples() if DATABASE.exists() else pd.read_csv(DATA/'samples.csv')
    expected = {f'NO{i}': 200 for i in range(1, 6)}
    if points.point_id.duplicated().any() or points.groupby('region_id').size().to_dict() != expected:
        raise ValueError('Use the original 1,000 points: 200 in each price area. Do not resample.')
    fingerprint = samples_hash(points)
    if 'grid_id' not in points or points.grid_id.isna().any():
        path = cache/f'grid_points_{fingerprint[:12]}.csv'
        if not path.exists():
            raise ValueError(f'Missing saved grid mapping: {path}. Use the folder from your original ERA5 download.')
        points = pd.read_csv(path, dtype={'grid_id': str})
        if samples_hash(points) != fingerprint:
            raise ValueError('The cached grid mapping belongs to different samples.')
    if points.grid_id.isna().any() or len(points) != 1000 or points.point_id.duplicated().any():
        raise ValueError('The grid mapping must contain all 1,000 unique sample IDs.')
    weights = points.area_weight.to_numpy(dtype=float)
    if not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError('Sample area weights must be finite and positive.')
    return points, fingerprint


def build_frames(points, regions, year, cache):
    dates = pd.date_range(f'{year}-01-01', f'{year+1}-01-01', freq='h', inclusive='left', tz='UTC')
    weights = area_weights(points, regions)
    needed = sorted(set().union(*(set(values.index) for values in weights.values())))
    paths = {}
    for cell in needed:
        path = (cache/f'{year}_{cell}.npz').resolve()
        if not path.is_relative_to(cache.resolve()):
            raise ValueError('Invalid cached cell ID.')
        paths[cell] = path
    missing = [path for path in paths.values() if not path.exists()]
    if missing:
        raise ValueError(f'{len(missing)} ERA5 cells are missing. Nothing was saved or published. '
                         'Restore the original weather_cache folder, or run prepare_all_weather.py --year '+str(year)+'.')
    totals = {region: np.zeros((len(dates), 2)) for region in weights}
    print(f'Reusing {len(needed)} cached cells. No weather API download.', flush=True)
    for cell, path in paths.items():
        with np.load(path, allow_pickle=False) as archive:
            values = np.asarray(archive['values'], dtype=float)
        if values.shape != (len(dates), 2) or not np.isfinite(values).all() or (values[:, 1] < 0).any():
            raise ValueError(f'Invalid ERA5 cell: {path.name}. Nothing was saved or published.')
        for region, region_weights in weights.items():
            totals[region] += values * float(region_weights.get(cell, 0))
    frames = {}
    for region, total in totals.items():
        frame = pd.DataFrame(total/weights[region].sum(), index=dates,
                             columns=['temperature_2m', 'precipitation'])
        frame.index.name = 'time'
        frames[region] = validate_weather(frame.reset_index(), region, year)
    return frames


def publish_frames(points, regions, frames, fingerprint, year, refresh=False):
    # These imports do not run unless publication is requested.
    from pymongo import MongoClient
    from settings import get_secret
    from publish_local import publish
    import geopandas as gpd

    locations = gpd.GeoSeries(gpd.points_from_xy(points.longitude, points.latitude), crs=4326)
    with MongoClient(get_secret('MONGO_URI'), tz_aware=True, serverSelectionTimeoutMS=15000) as client:
        client.admin.command('ping')
        db = client['nve']
        if db.era5_samples_v4.count_documents({'samples_hash': fingerprint}) != 1000:
            raise ValueError('Atlas does not contain these original 1,000 samples. Check your local folder and saved connection.')
        jobs = []
        for area in regions.itertuples():
            key = f'era5_{area.area_id}_{year}_n200_v4'
            digest = hashlib.sha256(area.geometry.wkb).hexdigest()
            existing = db.era5_datasets_v4.find_one({'_id': key})
            if existing and existing.get('samples_hash') not in (None, fingerprint):
                raise ValueError('An existing VASS dataset uses different samples. It was not replaced.')
            if existing and existing.get('status') == 'complete':
                if existing.get('boundary_hash') == digest:
                    print(f'{area.area_id}: already published; skipped.')
                    continue
                if not refresh:
                    raise ValueError(f'{area.area_id} already exists with different or unverified boundaries. '
                                     'Use --refresh-vass only if you intend to update that VASS dataset.')
            jobs.append((area, key, digest))
        # No writes occur until every dataset has passed the checks above.
        for area, key, digest in jobs:
            db.era5_datasets_v4.update_one({'_id': key}, {'$set': {
                'status': 'uploading', 'boundary_hash': digest,
                'boundary_status': getattr(area, 'boundary_status', 'unverified'),
                'boundary_basis': getattr(area, 'boundary_basis', 'Provided VASS polygons'),
                'source_codes': getattr(area, 'source_codes', '')}}, upsert=True)
            subset = points.loc[locations.covered_by(area.geometry)]
            publish(db, area.area_id, year, frames[area.area_id], subset, fingerprint)
        print('VASS publication complete. NO0, NO1–NO5, the original NO3 and Part 2 were not changed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, default=2024)
    parser.add_argument('--cache-dir', type=Path, default=DATA/'weather_cache')
    parser.add_argument('--publish', action='store_true', help='Upload VASS only, using the saved Atlas connection')
    parser.add_argument('--refresh-vass', action='store_true', help='Allow updating existing VASS data for these samples')
    args = parser.parse_args()
    if not 1940 <= args.year < pd.Timestamp.now().year:
        parser.error('Choose a complete historical year.')
    if args.refresh_vass and not args.publish:
        parser.error('--refresh-vass requires --publish.')
    try:
        regions = read_areas('VASS')
        points, fingerprint = cached_points(args.cache_dir)
        frames = build_frames(points, regions, args.year, args.cache_dir)
        if not DATABASE.exists():
            save_samples(points)
        for region, frame in frames.items():
            save_weather(region, args.year, frame)
            print(f'{region}: saved {len(frame)} hourly averages locally.')
        print('Boundary labels: '+', '.join(regions.name.astype(str)))
        if args.publish:
            publish_frames(points, regions, frames, fingerprint, args.year, args.refresh_vass)
            print('Reboot Streamlit to clear its cached data. Select this same year in the app.')
        else:
            print('Ready locally. Run again with --publish to upload only VASS.')
    except Exception as error:
        # Do not print connection strings or private driver exceptions.
        from pymongo.errors import PyMongoError
        if isinstance(error, PyMongoError):
            parser.exit(1, 'Atlas could not be reached or authenticated. Check the saved connection and Atlas Network Access.\n')
        if isinstance(error, (ValueError, FileNotFoundError, KeyError)):
            parser.exit(1, str(error)+'\n')
        raise


if __name__ == '__main__':
    main()

