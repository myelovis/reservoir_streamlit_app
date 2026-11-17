"""Create approximate VASS map areas from the Part 3 NVE regions."""
import argparse
import json
from pathlib import Path

import geopandas as gpd
import requests
import shapefile
from pyproj import CRS

URL = 'https://kart.nve.no/enterprise/rest/services/Mapservices/Administrasjon2/MapServer/0/query'
GROUPS = {'RS': 1, 'RO': 1, 'RV': 2, 'RM': 3, 'RN': 3}
NAMES = {1: 'East (approx.; RS + RØ)', 2: 'West (approx.; RV)',
         3: 'North (approx.; RM + RN)'}


def load_regions(source=None, encoding='utf-8'):
    if source is None:
        # Download five administrative regions, not weather or reservoir data.
        response = requests.get(URL, params={
            'where': '1=1', 'outFields': 'REGION', 'outSR': 4326,
            'returnGeometry': 'true', 'f': 'geojson',
        }, timeout=90)
        response.raise_for_status()
        data = response.json()
        if 'error' in data or not data.get('features'):
            raise ValueError('NVE returned no regions. Use your Part 3 shapefile instead.')
        return gpd.GeoDataFrame.from_features(data['features'], crs=4326)

    source = Path(source)
    if source.suffix.lower() in {'.geojson', '.json'}:
        data = json.loads(source.read_text(encoding='utf-8'))
        return gpd.GeoDataFrame.from_features(data['features'], crs=4326)
    if source.suffix.lower() != '.shp':
        raise ValueError('Choose a .shp or a WGS84 .geojson file.')
    for extension in ['.shx', '.dbf', '.prj']:
        if not source.with_suffix(extension).exists():
            raise ValueError(f'Keep {source.with_suffix(extension).name} beside the shapefile.')
    crs = CRS.from_wkt(source.with_suffix('.prj').read_text())
    with shapefile.Reader(str(source), encoding=encoding) as reader:
        return gpd.GeoDataFrame.from_features(reader.__geo_interface__['features'], crs=crs)


def merge_regions(regions, column='REGION'):
    columns = {str(name).upper(): name for name in regions.columns}
    if column.upper() not in columns:
        raise ValueError(f'Choose --column from: {list(regions.columns)}')
    codes = regions[columns[column.upper()]].astype(str).str.strip().str.upper()
    codes = codes.str.replace('Ø', 'O', regex=False).str.replace('Ö', 'O', regex=False)
    if set(codes) != set(GROUPS):
        raise ValueError(f'Expected RS, RØ/RO, RV, RM and RN. Found: {sorted(set(codes))}')
    if regions.crs is None or regions.geometry.isna().any() or regions.geometry.is_empty.any():
        raise ValueError('The source needs a CRS and non-empty polygons.')

    # Keep only geometry and the new number to avoid index/column conflicts.
    result = regions[['geometry']].reset_index(drop=True).copy()
    result['area_number'] = codes.map(GROUPS).to_numpy()
    result = result.to_crs(3035)
    result.geometry = result.geometry.make_valid()
    result = result.dissolve(by='area_number', as_index=False)
    result['area_type'] = 'VASS'
    result['area_id'] = 'VASS' + result.area_number.astype(str)
    result['name'] = result.area_number.map(NAMES)
    # This is an assignment approximation, not verified official VASS geometry.
    result['boundary_status'] = 'approximate'
    result['boundary_basis'] = 'Merged NVE administrative regions; VASS match unverified'
    result['source_codes'] = result.area_number.map({1: 'RS + RØ', 2: 'RV', 3: 'RM + RN'})
    result = result.to_crs(4326)
    if len(result) != 3 or not result.geometry.is_valid.all():
        raise ValueError('Could not create three valid merged polygons.')
    if not result.geometry.geom_type.isin(['Polygon', 'MultiPolygon']).all():
        raise ValueError('The source must contain polygon regions.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', help='Part 3 shapefile or GeoJSON; otherwise download from NVE')
    parser.add_argument('--column', default='REGION')
    parser.add_argument('--encoding', default='utf-8', help='Use cp1252 for an older shapefile if needed')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent/'data/VASS.geojson')
    parser.add_argument('--overwrite', action='store_true', help='Replace an existing boundary file')
    args = parser.parse_args()
    if args.output.exists() and not args.overwrite:
        parser.error('Output already exists. Use --overwrite only to replace it.')
    try:
        result = merge_regions(load_regions(args.source, args.encoding), args.column)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result.to_json(drop_id=True), encoding='utf-8')
    except (ValueError, OSError, requests.RequestException, shapefile.ShapefileException) as error:
        parser.exit(1, f'{error}\n')
    print(result[['area_id', 'name']].to_string(index=False))
    print(f'\nSaved: {args.output.resolve()}')
    print('Approximate boundaries only. No samples, weather or Atlas records were changed.')
    print('Upload data/VASS.geojson with the app and reboot it. VASS weather needs separate preparation.')


if __name__ == '__main__':
    main()
