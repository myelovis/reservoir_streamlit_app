"""Regression tests for Arrow display and read-only Part 4 weather reuse."""
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest
from reservoir_app import weather, reservoirs, tables, transfers
from reservoir_app.areas import weather_region_id
from reservoir_app.atlas import DatasetNotReady

ROOT = Path(__file__).resolve().parents[1]
AREAS = [('NO', 0), *[('EL', n) for n in range(1, 6)], *[('VASS', n) for n in range(1, 4)]]

def hourly(region='NO3', year=2024):
    dates = pd.date_range(f'{year}-01-01', f'{year+1}-01-01', freq='h', inclusive='left', tz='UTC')
    x = np.arange(len(dates))
    return pd.DataFrame({'time': dates, 'region_id': region, 'model': 'era5',
                         'temperature_2m': 5 + 10 * np.sin(x / 300),
                         'precipitation': 1 + np.sin(x / 17) ** 2})

class Cursor(list):
    def sort(self, key, direction):
        return Cursor(sorted(self, key=lambda row: row[key], reverse=direction < 0))

class Collection:
    # Deliberately no mutation methods: tests fail if the app tries to upload.
    def __init__(self, rows=()):
        self.rows = rows
        self.queries = []

    def find(self, query, projection=None):
        self.queries.append(query)
        def matches(row):
            for key, value in query.items():
                actual = row.get(key)
                if isinstance(value, dict):
                    if '$gte' in value and actual < value['$gte']:
                        return False
                    if '$lt' in value and actual >= value['$lt']:
                        return False
                elif actual != value:
                    return False
            return True
        return Cursor(dict(row) for row in self.rows if matches(row))

    def find_one(self, query):
        return next(iter(self.find(query)), None)

class Database(dict):
    def __getattr__(self, key):
        return self[key]

def publication(region='NO3', version=4):
    key = f'era5_{region}_2024' + ('_n200_v4' if version == 4 else '')
    frame = hourly(region).assign(dataset_id=key)
    meta = {'_id': key, 'region_id': region, 'year': 2024, 'model': 'era5',
            'status': 'complete', 'hours': len(frame), 'sample_count': 200 if version == 4 else 1000,
            'samples_hash': 'test', 'updated_at': 'fixed'}
    db = Database({name: Collection() for name in [
        'era5_datasets_v4', 'era5_hourly_v4', 'era5_datasets', 'era5_hourly']})
    suffix = '_v4' if version == 4 else ''
    db[f'era5_datasets{suffix}'] = Collection([meta])
    db[f'era5_hourly{suffix}'] = Collection(frame.to_dict('records'))
    return db

@pytest.fixture(autouse=True)
def clear_cache():
    weather.load_weather.clear()
    weather.available_weather_years.clear()
    yield
    weather.load_weather.clear()
    weather.available_weather_years.clear()

@pytest.mark.parametrize('kind,number', AREAS)
def test_exact_area_reuses_part4(kind, number):
    region = weather_region_id(kind, number)
    assert region == (f'NO{number}' if kind in ['NO', 'EL'] else f'VASS{number}')
    db = publication(region)
    with patch.object(weather, 'atlas_db', return_value=db):
        assert weather.available_weather_years(region) == [2024]
        result, source = weather.load_weather(region, 2024)
    assert len(result) == 8784
    assert 'Part 4' in source and region in source and '200 samples' in source
    assert not db.era5_hourly.queries

def test_original_dataset_remains_available():
    with patch.object(weather, 'atlas_db', return_value=publication(version=3)):
        frame, source = weather.load_weather('NO3', 2024)
    assert len(frame) == 8784 and 'Part 3' in source

def test_no_cross_region_fallback():
    with patch.object(weather, 'atlas_db', return_value=publication('NO3')):
        assert weather.available_weather_years('VASS1') == []
        with pytest.raises(DatasetNotReady):
            weather.load_weather('VASS1', 2024)

@pytest.mark.parametrize('issue', ['missing_hour', 'duplicate_hour', 'wrong_area', 'negative_rain', 'infinite'])
def test_weather_validation(issue):
    frame = hourly()
    if issue == 'missing_hour':
        frame = frame.iloc[:-1]
    elif issue == 'duplicate_hour':
        frame.loc[0, 'time'] = frame.loc[1, 'time']
    elif issue == 'wrong_area':
        frame.loc[0, 'region_id'] = 'NO1'
    elif issue == 'negative_rain':
        frame.loc[0, 'precipitation'] = -1
    else:
        frame.loc[0, 'temperature_2m'] = np.inf
    with pytest.raises(ValueError):
        weather.validate_weather(frame, 'NO3', 2024)

def reservoir_frame():
    dates = pd.date_range('2020-01-06', periods=300, freq='7D')
    frames = []
    for kind, number in AREAS:
        frame = pd.DataFrame({'date_id': dates, 'area_type': kind, 'area_number': number})
        for metric in reservoirs.METRICS:
            frame[metric] = .5 + .1 * np.sin(np.arange(len(dates)) / 8)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)

def test_arrow_sparklines_and_mongo_scalar_schema():
    month = reservoir_frame().query("area_type == 'NO'").head(4).set_index('date_id')
    summary = tables.reservoir_summary(month, reservoirs.METRICS)
    assert pa.Table.from_pandas(summary).num_rows == len(summary)
    assert all(isinstance(x, float) for values in summary['First month'] for x in values)
    assert pa.Table.from_pandas(month).num_rows == 4

def test_native_arrow_failure_has_readable_fallback():
    with patch.object(tables.st, 'dataframe', side_effect=ImportError('native library')), \
         patch.object(tables.st, 'caption'), patch.object(tables.st, 'html') as html:
        tables.display_dataframe(pd.DataFrame({'value': ['<script>bad</script>']}))
    assert '&lt;script&gt;' in html.call_args.args[0]

def test_reservoir_and_transfer_pages_render():
    frame = reservoir_frame()
    with patch.object(reservoirs, 'load_reservoirs', return_value=frame):
        at = AppTest.from_file(str(ROOT / 'pages/1_Reservoir_Table.py')).run(timeout=30)
        assert not at.exception
        assert len(at.dataframe) == 2
    dates = pd.date_range('2025-01-01', periods=24, freq='h', tz='UTC')
    records = pd.DataFrame({'time': list(dates) * 2, 'direction': ['in'] * 24 + ['out'] * 24,
                            'connection': 'NO2-DK1', 'power_mw': 100., 'hours': 1.,
                            'energy_mwh': 100., 'year': 2025})
    with patch.object(transfers, 'load_transfers', return_value=records):
        at = AppTest.from_file(str(ROOT / 'pages/5_Electricity_Transfers.py')).run(timeout=30)
        assert not at.exception
        assert len(at.dataframe) == 2

def test_weather_page_shared_selection_changes_region():
    frame = reservoir_frame()
    def load(region, year):
        return weather.validate_weather(hourly(region, year), region, year), f'Part 4 {region}'
    with patch.object(reservoirs, 'load_reservoirs', return_value=frame), \
         patch.object(weather, 'available_weather_years', return_value=[2024]), \
         patch.object(weather, 'load_weather', side_effect=load) as loader:
        at = AppTest.from_file(str(ROOT / 'pages/4_Weather_Outliers.py')).run(timeout=30)
        assert not at.exception
        assert loader.call_args.args == ('NO3', 2024)
        at.sidebar.radio[0].set_value('NO').run(timeout=30)
        assert not at.exception
        assert loader.call_args.args == ('NO0', 2024)
        at.sidebar.radio[0].set_value('VASS').run(timeout=30)
        assert not at.exception
        assert loader.call_args.args == ('VASS3', 2024)
        at.sidebar.selectbox[0].set_value(1).run(timeout=30)
        assert not at.exception
        assert loader.call_args.args == ('VASS1', 2024)
