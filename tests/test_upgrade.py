import numpy as np
import pandas as pd
import pytest
from region_tools import DATA, read_areas, clicked_area, area_weights
from weather_stats import weekly_weather, sliding_correlation, spc, lof
from forecast_tools import sarimax_forecast, ridge_forecast, future_weather
from weather_data import validate_weather
from plot_tools import forecast_animation


def test_samples_stay_in_their_regions():
    points = pd.read_csv(DATA/'samples.csv')
    assert points.groupby('region_id').size().to_dict()=={f'NO{i}':200 for i in range(1,6)}
    shapes = read_areas('EL')
    for row in points.itertuples():
        assert clicked_area(shapes,row.latitude,row.longitude).area_id==row.region_id
    assert len(points)==1000


def test_national_weights_account_for_region_size():
    points = pd.read_csv(DATA/'samples.csv')
    points['grid_id'] = points.region_id
    weights = area_weights(points,read_areas('NO'))['NO0']
    assert weights.max()>weights.min()*2
    expected = read_areas('EL').to_crs(3035).geometry.area.sum()
    assert weights.sum()==pytest.approx(expected,rel=1e-7)


def test_weekly_totals_and_partial_weeks():
    index = pd.date_range('2024-01-01',periods=24*17,freq='h',tz='UTC')
    hourly = pd.DataFrame({'temperature_2m':10.,'precipitation':.1},index=index)
    weekly = weekly_weather(hourly)
    assert weekly.iloc[0].precipitation==pytest.approx(16.8)
    assert weekly.iloc[0].temperature_2m==10
    assert weekly.iloc[-1].isna().all()


def test_lag_direction_and_gaps():
    rng = np.random.default_rng(4)
    x = rng.normal(size=100)
    frame = pd.DataFrame({'temperature_2m':x,'filling_change':pd.Series(x).shift(2).to_numpy()},
                         index=pd.date_range('2024-01-07',periods=100,freq='7D',tz='UTC'))
    correct = sliding_correlation(frame,'temperature_2m',lag=2,window=12)
    wrong = sliding_correlation(frame,'temperature_2m',lag=0,window=12)
    assert correct.correlation.dropna().mean()==pytest.approx(1)
    assert abs(wrong.correlation.dropna().mean())<.4
    frame.iloc[40,0]=np.nan
    assert sliding_correlation(frame,'temperature_2m',lag=0,window=12).correlation.iloc[40:52].isna().all()


def test_default_temperature_spc_and_lof():
    rng = np.random.default_rng(5)
    y = pd.Series(rng.normal(size=1000),index=pd.date_range('2024-01-01',periods=1000,freq='h',tz='UTC'))
    y.iloc[400]=50
    result = spc(y)
    assert result.flag.iloc[400]
    assert {'value','lower','upper','flag'}==set(result.columns)
    assert 'residual' not in result
    assert lof(y).flag.iloc[400]
    with pytest.raises(ValueError):
        spc(y.drop(y.index[200]))


def test_full_leap_year_validation():
    dates = pd.date_range('2024-01-01','2025-01-01',freq='h',inclusive='left',tz='UTC')
    frame = pd.DataFrame({'time':dates,'temperature_2m':4.,'precipitation':.1,'region_id':'VASS1','model':'era5'})
    assert len(validate_weather(frame,'VASS1',2024))==8784
    with pytest.raises(ValueError):
        validate_weather(frame.iloc[:-1],'VASS1',2024)
    with pytest.raises(ValueError):
        validate_weather(frame,'NO3',2024)


def test_recursive_forecasts_and_future_weather():
    dates = pd.date_range('2022-01-02',periods=110,freq='7D',tz='UTC')
    x = pd.DataFrame({'temperature_2m':np.sin(np.arange(110)/8)},index=dates)
    y = pd.Series(50+3*x.temperature_2m+np.arange(110)*.02,index=dates)
    future_dates = pd.date_range(dates[-1]+pd.Timedelta(days=7),periods=6,freq='7D')
    future = future_weather(x,future_dates)
    assert future.iloc[0,0]==pytest.approx(x.tail(4).mean().iloc[0])
    first,_ = sarimax_forecast(y,6,order=(1,0,0),exog=x,future_exog=future)
    changed = future.copy(); changed.iloc[-1,0]+=20
    second,_ = sarimax_forecast(y,6,order=(1,0,0),exog=x,future_exog=changed)
    assert first.forecast.iloc[0]==pytest.approx(second.forecast.iloc[0])
    assert first.forecast.iloc[-1]!=pytest.approx(second.forecast.iloc[-1])
    assert (first.lower<=first.forecast).all() and (first.forecast<=first.upper).all()
    ridge,_=ridge_forecast(y,6,exog=x,future_exog=future)
    assert ridge.index.equals(first.index)
    assert len(forecast_animation(y.tail(30),first,'Test').frames)==6
    with pytest.raises(ValueError):
        ridge_forecast(y,6,exog=x,future_exog=future.iloc[:-1])


def test_publisher_is_idempotent_and_keeps_old_collections():
    from publish_local import publish
    class Collection:
        def __init__(self): self.rows=[]
        def create_index(self,*args,**kwargs): pass
        def find_one(self,key): return next((r for r in self.rows if all(r.get(k)==v for k,v in key.items())),None)
        def update_one(self,key,update,upsert=False):
            row=self.find_one(key)
            if row is None: row=dict(key); self.rows.append(row)
            row.update(update['$set'])
        def bulk_write(self,operations,**kwargs):
            for operation in operations:self.update_one(operation._filter,operation._doc,True)
        def count_documents(self,key):return sum(all(r.get(k)==v for k,v in key.items()) for r in self.rows)
    class Database:
        def __init__(self): self.era5_hourly_v4=Collection(); self.era5_datasets_v4=Collection()
    db=Database()
    frame=pd.DataFrame({'temperature_2m':[1.,2.],'precipitation':[0.,.1]},index=pd.date_range('2024-01-01',periods=2,freq='h',tz='UTC'))
    points=pd.DataFrame(index=range(200))
    publish(db,'NO1',2024,frame,points,'abc')
    publish(db,'NO1',2024,frame,points,'abc')
    assert len(db.era5_hourly_v4.rows)==2
    assert db.era5_datasets_v4.rows[0]['sample_count']==200
    assert not hasattr(db,'era5_hourly')


def test_local_database_reuses_rows(tmp_path,monkeypatch):
    import local_store
    from region_tools import samples_hash
    monkeypatch.setattr(local_store,'DATABASE',tmp_path/'test.sqlite3')
    points=pd.read_csv(DATA/'samples.csv')
    local_store.save_samples(points)
    assert samples_hash(local_store.read_samples())==samples_hash(points)
    dates=pd.date_range('2024-01-01',periods=3,freq='h',tz='UTC')
    frame=pd.DataFrame({'temperature_2m':[1.,2.,3.],'precipitation':[0.,.1,.2]},index=dates)
    local_store.save_weather('NO1',2024,frame)
    local_store.save_weather('NO1',2024,frame)
    restored=local_store.read_weather('NO1',2024)
    assert len(restored)==3 and restored.temperature_2m.iloc[-1]==3
    changed=points.copy(); changed.loc[0,'latitude']+=.1
    with pytest.raises(ValueError):local_store.save_samples(changed)


def test_gaps_and_missing_weather_are_rejected():
    dates=pd.date_range('2024-01-07',periods=30,freq='7D',tz='UTC')
    y=pd.Series(np.arange(30,dtype=float),index=dates)
    with pytest.raises(ValueError):
        ridge_forecast(y.drop(dates[10]),2)
    with pytest.raises(ValueError):
        sarimax_forecast(y,2,exog=pd.DataFrame({'x':np.nan},index=dates))
    with pytest.raises(ValueError):
        future_weather(pd.DataFrame(),dates[:2])


def test_local_credentials_are_entered_only_once(tmp_path,monkeypatch,capsys):
    import settings,setup_local
    monkeypatch.setattr(settings,'CONFIG_FILE',tmp_path/'private'/'secrets.toml')
    monkeypatch.setattr(settings,'ROOT',tmp_path)
    monkeypatch.delenv('MONGO_URI',raising=False)
    monkeypatch.delenv('ENTSOE_TOKEN',raising=False)
    settings.saved_settings.cache_clear()
    values=iter(['mongodb://user:test-password@localhost/test','test-entsoe-token'])
    setup_local.configure(ask=lambda prompt:next(values))
    def never_ask(prompt):raise AssertionError('A saved secret was requested again.')
    setup_local.configure(ask=never_ask)
    assert settings.get_secret('ENTSOE_TOKEN')=='test-entsoe-token'
    assert settings.get_secret('MONGO_URI').startswith('mongodb://')
    assert 'test-password' not in capsys.readouterr().out
    settings.saved_settings.cache_clear()


def test_uploader_does_not_download_weather():
    import publish_local
    assert not hasattr(publish_local,'requests')
    assert not hasattr(publish_local,'api_request')


def test_upload_of_local_sample_database_is_repeatable(monkeypatch):
    import publish_local
    points=pd.read_csv(DATA/'samples.csv')
    class Samples:
        def __init__(self):self.rows={}
        def create_index(self,*a,**k):pass
        def bulk_write(self,operations,**kwargs):
            for operation in operations:self.rows[operation._filter['point_id']]=operation._doc['$set']
        def count_documents(self,query):return sum(row['samples_hash']==query['samples_hash'] for row in self.rows.values())
    class Metadata:
        def find(self,*args):return []
    class Database:
        era5_samples_v4=Samples()
        era5_datasets_v4=Metadata()
    db=Database()
    class Client:
        def __init__(self,*a,**k):self.admin=self
        def command(self,*a):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def __getitem__(self,key):return db
    monkeypatch.setattr(publish_local,'MongoClient',Client)
    monkeypatch.setattr(publish_local,'get_secret',lambda key:'test-only')
    monkeypatch.setattr(publish_local,'read_samples',lambda:points.copy())
    publish_local.main(samples_only=True)
    publish_local.main(samples_only=True)
    assert len(db.era5_samples_v4.rows)==1000

