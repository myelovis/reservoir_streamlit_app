"""No network calls. Check that diagnostics are useful and hide secrets."""
import json
import unittest
from unittest.mock import patch
import weather_data
import settings


class StatusTests(unittest.TestCase):
    def test_report_separates_visible_records_from_usable_years(self):
        class Collection:
            def find(self, query, projection):
                assert query == {'region_id': 'NO3'}
                assert projection == {'_id':0, 'year':1, 'model':1, 'status':1}
                return [{'year':1996, 'model':'era5', 'status':'complete'},
                        {'year':'1997', 'model':'era5', 'status':'complete'},
                        {'year':1998, 'model':'era5', 'status':'uploading'}]
        class Database:
            name = 'nve'
            def __getitem__(self, name):
                return Collection()
        with patch.object(weather_data, 'atlas_db', return_value=Database()), \
             patch.object(settings, 'get_secret', return_value='mongodb+srv://private_user:private_password@example.invalid/'):
            report = weather_data.weather_date_status('NO3')
        collection = report['collections']['era5_history_v1']
        self.assertEqual(collection['region_documents'], 3)
        self.assertEqual(collection['usable_years'], [1996])
        self.assertEqual(collection['year_types'], ['int','str'])
        self.assertEqual(len(report['connection_id']), 12)
        for private in ['private_user', 'private_password', 'example.invalid']:
            self.assertNotIn(private, json.dumps(report))


if __name__ == '__main__':
    unittest.main()

