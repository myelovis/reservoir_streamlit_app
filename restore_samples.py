"""Recover the original 1,000 points from Atlas. Never sample again."""
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from pymongo import MongoClient
from settings import get_secret
from region_tools import DATA, samples_hash
from local_store import save_samples


def check_samples(points):
    required = ['point_id', 'region_id', 'latitude', 'longitude', 'area_weight']
    if not set(required).issubset(points.columns):
        raise ValueError('The saved samples are missing required fields.')
    if len(points) != 1000 or points.point_id.duplicated().any():
        raise ValueError('Expected the original 1,000 unique points.')
    if points.groupby('region_id').size().to_dict() != {f'NO{i}': 200 for i in range(1, 6)}:
        raise ValueError('Expected 200 original points in each NO1–NO5 area.')
    numbers = points[['latitude', 'longitude', 'area_weight']].to_numpy(float)
    if not np.isfinite(numbers).all() or (points.area_weight <= 0).any():
        raise ValueError('The original coordinates or area weights are invalid.')
    if not points.latitude.between(-90, 90).all() or not points.longitude.between(-180, 180).all():
        raise ValueError('Coordinates must be longitude and latitude in degrees.')
    return points.sort_values('point_id').reset_index(drop=True)


def restore():
    with MongoClient(get_secret('MONGO_URI'), tz_aware=True, serverSelectionTimeoutMS=15000) as client:
        db = client['nve']
        points = check_samples(pd.DataFrame(list(db.era5_samples_v4.find({}, {'_id': 0}))))
        fingerprint = samples_hash(points)
        for meta in db.era5_datasets_v4.find({'status': 'complete'}):
            if meta.get('samples_hash') != fingerprint:
                raise ValueError('Atlas weather and sample coordinates do not match. No local data was replaced.')
        if 'samples_hash' in points and not points.samples_hash.eq(fingerprint).all():
            raise ValueError('Atlas sample fingerprints do not match their coordinates.')
    # save_samples also refuses to replace samples linked to other local weather.
    save_samples(points)
    path = DATA/'samples.csv'
    different = False
    if path.exists():
        try:
            different = samples_hash(pd.read_csv(path)) != fingerprint
        except (ValueError, KeyError, pd.errors.ParserError):
            different = True
    if different:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        backup = path.with_name(f'samples_before_restore_{stamp}.csv')
        backup.write_bytes(path.read_bytes())
        print(f'Kept the previous CSV as {backup.name}.')
    points.to_csv(path, index=False)
    print('Restored the original 1,000 points to data/prepared.sqlite3 and data/samples.csv.')
    print('No Atlas records were changed. Existing weather caches were kept.')


if __name__ == '__main__':
    try:
        restore()
    except Exception as error:
        from pymongo.errors import PyMongoError
        if isinstance(error, PyMongoError):
            raise SystemExit('Atlas could not be read. Check the saved connection and Atlas Network Access.') from None
        raise
