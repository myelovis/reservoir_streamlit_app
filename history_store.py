"""Small regional files and one compressed Atlas document per year."""
from io import BytesIO
from pathlib import Path
import hashlib
from zipfile import BadZipFile
import numpy as np
import pandas as pd

VARIABLES = ['temperature_2m', 'precipitation']
COLLECTION = 'era5_history_v1'


def year_dates(year):
    return pd.date_range(f'{year}-01-01', f'{year+1}-01-01', freq='h', inclusive='left', tz='UTC')


def encode(values, year):
    values = np.asarray(values, dtype=np.float64)
    if values.shape != (len(year_dates(year)), 2) or not np.isfinite(values).all() or (values[:, 1] < 0).any():
        raise ValueError('A history year needs complete hourly ERA5 temperature and precipitation.')
    buffer = BytesIO()
    np.savez_compressed(buffer, values=values)
    return buffer.getvalue()


def decode(payload, year):
    try:
        with np.load(BytesIO(bytes(payload)), allow_pickle=False) as saved:
            values = saved['values']
    except (ValueError, OSError, KeyError, BadZipFile) as error:
        raise ValueError('A cached or published history file is damaged. Restore that file before continuing.') from error
    if values.shape != (len(year_dates(year)), 2) or not np.isfinite(values).all() or (values[:, 1] < 0).any():
        raise ValueError('Stored history has missing hours or invalid values.')
    return pd.DataFrame(values, index=year_dates(year), columns=VARIABLES).rename_axis('time')


def publish_year(db, folder, manifest, year):
    from bson.binary import Binary
    collection = db[COLLECTION]
    for region, info in manifest['regions'].items():
        path = Path(folder)/f'{year}_{region}.npz'
        if not path.exists():
            raise ValueError(f'Prepare all regional files for {year} before publication.')
        payload = path.read_bytes()
        decode(payload, year)
        digest = hashlib.sha256(payload).hexdigest()
        key = f'era5_{region}_{year}_subset25_v1'
        old = collection.find_one({'_id': key}, {'payload': 0})
        if old and (old.get('plan_hash') != manifest['plan_hash'] or old.get('payload_hash') != digest):
            raise ValueError(f'{region}, {year}: different history already exists. It was not replaced.')
    for region, info in manifest['regions'].items():
        payload = (Path(folder)/f'{year}_{region}.npz').read_bytes()
        key = f'era5_{region}_{year}_subset25_v1'
        record = dict(_id=key, status='complete', region_id=region, year=year, model='era5',
            hours=len(year_dates(year)), properties=VARIABLES, sample_count=len(info['point_ids']),
            source_sample_count=1000, source_samples_hash=manifest['source_samples_hash'],
            plan_hash=manifest['plan_hash'], payload_hash=hashlib.sha256(payload).hexdigest(),
            format='npz-float64-v1', payload=Binary(payload),
            sampling_method='fixed subset of original points; area-weighted regional mean',
            point_ids=info['point_ids'], boundary_status=info['boundary_status'],
            boundary_hash=info['boundary_hash'], updated_at=pd.Timestamp.now(tz='UTC').to_pydatetime())
        result = collection.update_one({'_id': key}, {'$setOnInsert': record}, upsert=True)
        saved = collection.find_one({'_id': key}, {'payload_hash': 1, 'plan_hash': 1, 'hours': 1})
        if saved is None or saved.get('payload_hash') != record['payload_hash'] or saved.get('plan_hash') != record['plan_hash']:
            raise ValueError('History verification failed. No existing datasets were replaced.')
        print(f'{year} {region}: '+('published.' if result.upserted_id else 'already published; skipped.'), flush=True)
