"""Upload the prepared local database. No weather API calls happen here."""
import argparse
import pandas as pd
from pymongo import MongoClient, UpdateOne
from settings import get_secret
from local_store import read_samples, read_weather
from region_tools import DATA, read_areas, samples_hash
from weather_data import validate_weather


def publish(db, region_id, year, frame, points, fingerprint):
    key = f'era5_{region_id}_{year}_n200_v4'
    existing = db.era5_datasets_v4.find_one({'_id':key})
    if existing and existing.get('status')=='complete':
        if existing.get('samples_hash')!=fingerprint:
            raise ValueError('A completed dataset uses different samples. Keep it and use a new dataset version.')
        print(f'{region_id}: already complete; no rows added.')
        return
    db.era5_hourly_v4.create_index([('dataset_id',1),('time',1)],unique=True)
    db.era5_datasets_v4.update_one({'_id':key},{'$set':{'status':'uploading'}},upsert=True)
    for start in range(0,len(frame),1000):
        operations = []
        for stamp,row in frame.iloc[start:start+1000].iterrows():
            identity = {'dataset_id':key,'time':stamp.to_pydatetime()}
            record = {**identity,'region_id':region_id,'model':'era5',**row.to_dict()}
            operations.append(UpdateOne(identity,{'$set':record},upsert=True))
        db.era5_hourly_v4.bulk_write(operations,ordered=False)
    count = db.era5_hourly_v4.count_documents({'dataset_id':key})
    if count!=len(frame):
        raise ValueError('Atlas verification failed. Run again to finish this dataset.')
    db.era5_datasets_v4.update_one({'_id':key},{'$set':{
        'status':'complete','region_id':region_id,'year':year,'model':'era5','hours':count,
        'sample_count':len(points),'source_sample_count':1000,'samples_hash':fingerprint,
        'sampling_method':'200 uniform points per price area; area weights for derived areas',
        'properties':list(frame.columns),'updated_at':pd.Timestamp.now(tz='UTC').to_pydatetime()}},upsert=True)
    print(f'Verified {region_id}: {count} hourly averages from {len(points)} points.')



def upload_samples(db, points, fingerprint):
    for meta in db.era5_datasets_v4.find({'status':'complete'}):
        if meta.get('samples_hash')!=fingerprint:
            raise ValueError('Completed data uses different samples. Use a new dataset version.')
    db.era5_samples_v4.create_index('point_id',unique=True)
    operations=[UpdateOne({'point_id':row['point_id']},{'$set':{**row,'samples_hash':fingerprint}},upsert=True)
                for row in points.to_dict('records')]
    db.era5_samples_v4.bulk_write(operations,ordered=False)
    count=db.era5_samples_v4.count_documents({'samples_hash':fingerprint})
    if count!=1000:
        raise ValueError('Atlas sample count is not 1,000. Check the local sample table.')
    print('Verified 1,000 sample coordinates in nve.era5_samples_v4.')


def main(year=2024,samples_only=False):
    points=read_samples()
    if points.groupby('region_id').size().to_dict()!={f'NO{i}':200 for i in range(1,6)}:
        raise ValueError('Expected 200 points in each of the five price areas.')
    fingerprint=samples_hash(points)
    with MongoClient(get_secret('MONGO_URI'),tz_aware=True,serverSelectionTimeoutMS=15000) as client:
        client.admin.command('ping')
        db=client['nve']
        upload_samples(db,points,fingerprint)
        if samples_only:
            return
        import geopandas as gpd
        locations=gpd.GeoSeries(gpd.points_from_xy(points.longitude,points.latitude),crs=4326)
        for kind in ['EL','NO','VASS']:
            if not (DATA/f'{kind}.geojson').exists():
                print(f'{kind} skipped: add its official boundary file first.')
                continue
            for area in read_areas(kind).itertuples():
                key=f'era5_{area.area_id}_{year}_n200_v4'
                meta=db.era5_datasets_v4.find_one({'_id':key,'status':'complete'})
                if meta and meta.get('samples_hash')==fingerprint:
                    print(f'{area.area_id}: already complete, skipped.')
                    continue
                frame=read_weather(area.area_id,year)
                checked=validate_weather(frame.reset_index(),area.area_id,year)
                subset=points.loc[locations.covered_by(area.geometry)]
                publish(db,area.area_id,year,checked,subset,fingerprint)
    print('Upload done. Original NO3 and Part 2 collections were kept.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year',type=int,default=2024)
    parser.add_argument('--samples-only',action='store_true')
    args=parser.parse_args()
    main(args.year,args.samples_only)

