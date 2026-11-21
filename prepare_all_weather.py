"""Prepare weather in local SQLite. No database credentials are needed."""
import argparse
import time
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from region_tools import DATA, read_areas, area_weights, samples_hash
from local_store import read_samples, save_samples, save_weather

URL = 'https://archive-api.open-meteo.com/v1/archive'
VARIABLES = ['temperature_2m','precipitation']
CACHE = DATA / 'weather_cache'


def api_request(session, points, start, end):
    response = session.get(URL,params={
        'latitude':','.join(points.latitude.astype(str)),
        'longitude':','.join(points.longitude.astype(str)),
        'start_date':start,'end_date':end,'hourly':','.join(VARIABLES),
        'models':'era5','timezone':'GMT','cell_selection':'nearest',
        'elevation':','.join(['nan']*len(points))},timeout=180)
    if response.status_code==429:
        raise RuntimeError('Open-Meteo rate limit reached. Cached cells are safe. Run this again later to resume.')
    response.raise_for_status()
    payload = response.json()
    payload = payload if isinstance(payload,list) else [payload]
    if len(payload)!=len(points) or any('hourly' not in item for item in payload):
        raise ValueError('Open-Meteo did not return every requested location.')
    return payload


def locate_cells(points, year, fingerprint, session):
    path = CACHE / f'grid_points_{fingerprint[:12]}.csv'
    if path.exists():
        return pd.read_csv(path,dtype={'grid_id':str})
    rows = []
    for start in range(0,len(points),50):
        batch = points.iloc[start:start+50]
        data = api_request(session,batch,f'{year}-01-01',f'{year}-01-01')
        for point,item in zip(batch.to_dict('records'),data):
            point.update(grid_latitude=float(item['latitude']),grid_longitude=float(item['longitude']))
            point['grid_id'] = f"{item['latitude']:.6f}_{item['longitude']:.6f}"
            rows.append(point)
        print(f'Located {min(start+50,len(points))}/{len(points)} sample points.',flush=True)
        time.sleep(1)
    result = pd.DataFrame(rows)
    result.to_csv(path,index=False)
    return result


def cell_file(grid_id, year):
    return CACHE / f'{year}_{grid_id}.npz'


def download_cells(points, year, session):
    cells = points.drop_duplicates('grid_id').copy()
    cells['latitude'], cells['longitude'] = cells.grid_latitude,cells.grid_longitude
    needed = cells.loc[~cells.grid_id.map(lambda cell:cell_file(cell,year).exists())]
    expected = pd.date_range(f'{year}-01-01',f'{year+1}-01-01',freq='h',inclusive='left',tz='UTC')
    for start in range(0,len(needed),5):
        batch = needed.iloc[start:start+5]
        data = api_request(session,batch,f'{year}-01-01',f'{year}-12-31')
        for point,item in zip(batch.itertuples(),data):
            dates = pd.DatetimeIndex(pd.to_datetime(item['hourly']['time'],utc=True))
            values = np.column_stack([item['hourly'][column] for column in VARIABLES]).astype(float)
            if not dates.equals(expected) or not np.isfinite(values).all() or (values[:,1]<0).any():
                raise ValueError('An ERA5 cell has missing hours or invalid values. Nothing was published.')
            np.savez_compressed(cell_file(point.grid_id,year),values=values)
        print(f'Cached {min(start+5,len(needed))}/{len(needed)} missing cells.',flush=True)
        time.sleep(1)
    return expected


def regional_average(weights, year, dates):
    total = np.zeros((len(dates),len(VARIABLES)))
    for grid_id,weight in weights.items():
        with np.load(cell_file(grid_id,year)) as cell:
            total += cell['values']*weight
    return pd.DataFrame(total/weights.sum(),index=dates,columns=VARIABLES)


def main(year):
    if not 1940 <= year < pd.Timestamp.now().year:
        raise ValueError('Choose a complete historical year, from 1940 to last year.')
    CACHE.mkdir(parents=True,exist_ok=True)
    points=read_samples()
    if points.groupby('region_id').size().to_dict()!={f'NO{i}':200 for i in range(1,6)}:
        raise ValueError('Run prepare_regions.py with 200 points in each of NO1 to NO5.')
    fingerprint=samples_hash(points)
    session=requests.Session()
    session.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=2,status_forcelist=[500,502,503,504])))
    points=locate_cells(points,year,fingerprint,session)
    save_samples(points)
    dates=download_cells(points,year,session)
    regions=pd.concat([read_areas('EL'),read_areas('NO')],ignore_index=True)
    if (DATA/'VASS.geojson').exists():
        regions=pd.concat([regions,read_areas('VASS')],ignore_index=True)
    else:
        print('VASS skipped: add the official water-area boundaries first.')
    for region_id,weights in area_weights(points,regions).items():
        frame=regional_average(weights,year,dates)
        frame.index.name='time'
        save_weather(region_id,year,frame)
        print(f'Saved {region_id}: {len(frame)} hourly rows to local SQLite.')
    print('Local preparation done. Run publish_local.py to upload. No Atlas data was changed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year',type=int,default=2024)
    args=parser.parse_args()
    main(args.year)

