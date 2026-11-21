"""Read-only check using the saved connection. No weather download."""
import json
import argparse
from weather_data import weather_date_status

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--region', choices=[f'NO{i}' for i in range(6)]+['VASS1','VASS2','VASS3'], default='NO3')
    args = parser.parse_args()
    try:
        print(json.dumps(weather_date_status(args.region), indent=2))
    except Exception:
        raise SystemExit('Could not read Atlas metadata. Check your saved connection and database permissions.') from None
