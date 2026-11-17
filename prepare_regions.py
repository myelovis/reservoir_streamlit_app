"""Run once: convert boundaries and save 200 points per price area."""
import argparse
import json
from pathlib import Path
import geopandas as gpd
import shapefile
from pyproj import CRS
from region_tools import DATA, sample_regions


def convert(source, kind, id_column, mapping=None):
    source = Path(source)
    if source.suffix.lower() in ('.json','.geojson'):
        areas = gpd.GeoDataFrame.from_features(json.loads(source.read_text(encoding='utf-8'))['features'],crs=4326)
    else:
        projection = source.with_suffix('.prj')
        if not projection.exists():
            raise ValueError('Keep the .prj file beside the shapefile.')
        crs = CRS.from_wkt(projection.read_text())
        with shapefile.Reader(str(source),encoding='utf-8') as reader:
            areas = gpd.GeoDataFrame.from_features(reader.__geo_interface__['features'],crs=crs)
    if areas.crs is None:
        raise ValueError('The source has no CRS. Keep the .prj file with the shapefile.')
    if id_column not in areas:
        raise ValueError(f'Choose an ID column from: {list(areas.columns)}')
    code = areas[id_column].astype(str).str.replace(' ', '', regex=False)
    if mapping:
        code = code.map(mapping)
        if code.isna().any():
            raise ValueError('The mapping does not cover every source ID.')
    areas['area_number'] = code.str.extract(r'(\d+)$')[0].astype(int)
    areas['area_type'] = kind
    areas['area_id'] = ('NO' if kind == 'EL' else kind) + areas.area_number.astype(str)
    if kind=='VASS' and set(areas.area_id)!={'VASS1','VASS2','VASS3'}:
        raise ValueError('This app needs the three published VASS areas. Provide their official combined boundaries, not four separate descriptive regions.')
    areas['name'] = areas.area_id
    areas = areas[['area_id', 'area_type', 'area_number', 'name', 'geometry']]
    areas = areas.to_crs(3035).dissolve(by='area_id', as_index=False)
    areas.geometry = areas.geometry.make_valid()
    areas = areas.to_crs(4326)
    DATA.mkdir(exist_ok=True)
    (DATA/f'{kind}.geojson').write_text(areas.to_json(drop_id=True),encoding='utf-8')
    return areas


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--electricity', default='geo-nve-atlas_data/electricity_NO1_NO5.shp')
    parser.add_argument('--id-column', default='region')
    parser.add_argument('--water', help='Optional official VASS shapefile or GeoJSON')
    parser.add_argument('--water-id', default='area_number')
    parser.add_argument('--points', type=int, default=200)
    args = parser.parse_args()
    electricity = convert(args.electricity, 'EL', args.id_column)
    if set(electricity.area_id) != {f'NO{i}' for i in range(1, 6)}:
        raise ValueError('Expected the five price areas NO1 to NO5.')
    national = electricity.dissolve().reset_index(drop=True)
    national = national.assign(area_id='NO0', area_type='NO', area_number=0, name='Norway')
    (DATA/'NO.geojson').write_text(national.to_json(drop_id=True),encoding='utf-8')
    if args.water:
        convert(args.water, 'VASS', args.water_id)
    points = sample_regions(electricity, n=args.points)
    points.to_csv(DATA / 'samples.csv', index=False)
    from local_store import save_samples
    save_samples(points)
    print(f'Saved {len(points)} points: {args.points} in each price area.')
    print('NO is the union of the price-area boundaries. VASS needs its own official file.')
