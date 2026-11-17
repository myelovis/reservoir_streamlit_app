"""Optional: update reservoir observations. Reuse the saved MongoDB setting."""
import argparse
from uuid import uuid4
import pandas as pd
import requests
from pymongo import UpdateOne
from atlas_data import atlas_db
from reservoir_data import prepare_reservoirs


def publish_reservoirs():
    url='https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData'
    response=requests.get(url,timeout=120)
    response.raise_for_status()
    records=response.json()
    prepare_reservoirs(records)
    db=atlas_db()
    publication_id=uuid4().hex
    db.reservoir_weekly.create_index([('omrType',1),('omrnr',1),('dato_Id',1)],unique=True)
    db.reservoir_datasets.update_one({'_id':'current'},{'$set':{'status':'uploading'}},upsert=True)
    for start in range(0,len(records),1000):
        operations=[]
        for row in records[start:start+1000]:
            key={name:row[name] for name in ['omrType','omrnr','dato_Id']}
            operations.append(UpdateOne(key,{'$set':{**row,'publication_id':publication_id}},upsert=True))
        db.reservoir_weekly.bulk_write(operations,ordered=False)
    count=db.reservoir_weekly.count_documents({'publication_id':publication_id})
    if count!=len(records):
        raise ValueError('The upload is incomplete. Run this command again.')
    db.reservoir_datasets.update_one({'_id':'current'},{'$set':{'status':'complete',
        'publication_id':publication_id,'rows':count,'source':url,
        'updated_at':pd.Timestamp.now(tz='UTC').to_pydatetime()}},upsert=True)
    print(f'Verified {count} reservoir records. Weather and Part 2 collections were kept.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reservoirs',action='store_true',required=True)
    parser.parse_args()
    publish_reservoirs()
