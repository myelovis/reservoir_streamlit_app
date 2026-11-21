"""Read prepared weather from Atlas. Keep old NO3 data available."""
import numpy as np
import pandas as pd
import streamlit as st
from atlas_data import atlas_db, DatasetNotReady
from weather_stats import PROPERTIES


@st.cache_data(ttl=300, max_entries=32, show_spinner=False)
def weather_years(region_id):
    """Read year labels only. Do not download the weather payloads."""
    db = atlas_db()
    years = set()
    for name in ['era5_datasets_v4', 'era5_datasets', 'era5_history_v1']:
        query = {'region_id': region_id, 'model': 'era5', 'status': 'complete'}
        for record in db[name].find(query, {'_id': 0, 'year': 1}):
            year = record.get('year')
            if isinstance(year, (int, np.integer)) and not isinstance(year, bool) and 1940 <= year <= pd.Timestamp.now(tz='Europe/Paris').year:
                years.add(int(year))
    return sorted(years)


def validate_weather(frame, region_id, year):
    frame = frame.copy()
    if not {'time', 'temperature_2m', 'precipitation'}.issubset(frame.columns):
        raise ValueError('Weather needs time, temperature_2m and precipitation.')
    if 'region_id' in frame and not frame.region_id.eq(region_id).all():
        raise ValueError('The weather belongs to a different region.')
    if 'model' in frame and not frame.model.eq('era5').all():
        raise ValueError('Only ERA5 historical reanalysis is accepted.')
    frame['time'] = pd.to_datetime(frame.time, utc=True)
    frame = frame.set_index('time').sort_index()
    expected = pd.date_range(f'{year}-01-01', f'{year+1}-01-01', freq='h', inclusive='left', tz='UTC')
    if not frame.index.equals(expected):
        raise ValueError(f'The {year} dataset needs all {len(expected)} unique hourly rows.')
    columns = [column for column in PROPERTIES if column in frame]
    frame = frame[columns].apply(pd.to_numeric)
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError('Weather contains missing or infinite values. Prepare it again.')
    for column in set(columns)-{'temperature_2m'}:
        if frame[column].lt(0).any():
            raise ValueError(f'{column} cannot be negative.')
    return frame


@st.cache_data(ttl=600, max_entries=40, show_spinner=False)
def load_weather(region_id, year):
    db = atlas_db()
    key = f'era5_{region_id}_{year}_n200_v4'
    meta = db.era5_datasets_v4.find_one({'_id': key})
    if meta and meta.get('status') == 'complete':
        query = {'dataset_id': key}
        collection, metadata = db.era5_hourly_v4, db.era5_datasets_v4
    else:
        key = f'era5_{region_id}_{year}'
        meta = db.era5_datasets.find_one({'_id': key})
        query = {'region_id': region_id, 'model': 'era5', 'time': {
            '$gte': pd.Timestamp(f'{year}-01-01', tz='UTC').to_pydatetime(),
            '$lt': pd.Timestamp(f'{year+1}-01-01', tz='UTC').to_pydatetime()}}
        collection, metadata = db.era5_hourly, db.era5_datasets
    if not meta or meta.get('status') != 'complete':
        from history_store import COLLECTION, decode
        key = f'era5_{region_id}_{year}_subset25_v1'
        history = db[COLLECTION].find_one({'_id': key, 'status': 'complete'})
        if history is not None:
            if (history.get('model') != 'era5' or history.get('region_id') != region_id
                    or history.get('year') != year or history.get('format') != 'npz-float64-v1'
                    or history.get('sample_count', 0) < 25
                    or history.get('properties') != ['temperature_2m', 'precipitation']):
                raise ValueError('History metadata does not match the chosen region and year.')
            import hashlib
            payload = history.get('payload', b'')
            if hashlib.sha256(payload).hexdigest() != history.get('payload_hash'):
                raise ValueError('The compressed history did not pass its integrity check.')
            result = decode(payload, year)
            if len(result) != history.get('hours'):
                raise ValueError('History hour count does not match its metadata.')
            note = ' · approximate administrative-region boundaries' if history.get('boundary_status') == 'approximate' else ''
            return result, (f'Atlas · {region_id} · {year} · {history["sample_count"]} fixed-subset samples'
                            ' · area-weighted mean'+note)
        if region_id.startswith('VASS'):
            raise DatasetNotReady(f'No ERA5 weather is published for {region_id} in {year}. '
                                  'Its map boundary does not include weather observations. '
                                  'Choose a prepared region/year while the app owner publishes VASS weather.')
        raise DatasetNotReady(f'Prepare {region_id}, {year} locally, then run publish_local.py --year {year}.')
    count = meta.get('sample_count', meta.get('source_sample_count', 0))
    if count < 1 or meta.get('region_id') != region_id or meta.get('year') != year or meta.get('model') != 'era5':
        raise ValueError('Weather metadata does not match the selected dataset.')
    records = list(collection.find(query, {'_id': 0}).sort('time', 1))
    after = metadata.find_one({'_id': key})
    if not after or after.get('status') != 'complete' or after.get('updated_at') != meta.get('updated_at'):
        raise DatasetNotReady('Weather is being updated. Please try again later.')
    result = validate_weather(pd.DataFrame(records), region_id, year)
    if meta.get('hours') != len(result):
        raise ValueError('Weather row count does not match its metadata.')
    method = meta.get('sampling_method', 'original samples')
    note = ' · approximate administrative-region boundaries' if meta.get('boundary_status') == 'approximate' else ''
    return result, f'Atlas · {region_id} · {year} · {count} samples · {method}{note}'


@st.cache_data(ttl=600, max_entries=4, show_spinner=False)
def load_period(region_id, start, end):
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    parts, sources = [], []
    for year in range(start.year, end.year+1):
        values, source = load_weather(region_id, year)
        parts.append(values)
        sources.append(source)
    return pd.concat(parts).loc[str(start.date()):str(end.date())], '; '.join(sources)

