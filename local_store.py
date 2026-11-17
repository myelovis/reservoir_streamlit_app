"""A small SQLite database for local preparation."""
from contextlib import closing
import sqlite3
import pandas as pd
from region_tools import DATA, samples_hash

DATABASE = DATA / 'prepared.sqlite3'


def save_samples(points):
    if points.point_id.duplicated().any():
        raise ValueError('Sample point IDs must be unique.')
    DATABASE.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(DATABASE)) as connection:
        tables={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if {'samples','hourly'}.issubset(tables):
            old=pd.read_sql_query('SELECT * FROM samples',connection)
            if samples_hash(old)!=samples_hash(points) and connection.execute('SELECT COUNT(*) FROM hourly').fetchone()[0]:
                raise ValueError('This local database has weather for different samples. Keep it and create a new version.')
        points.to_sql('samples',connection,index=False,if_exists='replace')
        connection.execute('CREATE UNIQUE INDEX sample_id ON samples(point_id)')
        connection.commit()


def save_weather(region_id, year, frame):
    with closing(sqlite3.connect(DATABASE)) as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS hourly (region_id TEXT, year INTEGER, time TEXT, temperature_2m REAL, precipitation REAL, PRIMARY KEY(region_id,year,time))')
        rows = [(region_id,int(year),stamp.isoformat(),float(row.temperature_2m),float(row.precipitation)) for stamp,row in frame.iterrows()]
        connection.executemany('INSERT OR REPLACE INTO hourly VALUES (?,?,?,?,?)',rows)
        connection.commit()


def read_samples():
    if not DATABASE.exists():
        raise ValueError('Run prepare_regions.py first.')
    with closing(sqlite3.connect(DATABASE)) as connection:
        return pd.read_sql_query('SELECT * FROM samples ORDER BY point_id',connection)


def read_weather(region_id, year):
    with closing(sqlite3.connect(DATABASE)) as connection:
        if not connection.execute("SELECT name FROM sqlite_master WHERE name='hourly'").fetchone():
            raise ValueError('Run prepare_all_weather.py to fill the local weather table first.')
        frame = pd.read_sql_query('SELECT time,temperature_2m,precipitation FROM hourly WHERE region_id=? AND year=? ORDER BY time',connection,params=(region_id,int(year)))
    frame['time'] = pd.to_datetime(frame.time,utc=True)
    return frame.set_index('time')
