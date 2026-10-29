"""Run once outside Streamlit: python prepare_weather.py --region NO3 --year 2024"""
import argparse
from weather_data import prepare_weather

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=[f"NO{i}" for i in range(1, 6)], default="NO3")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    frame = prepare_weather(args.region, args.year)
    print(f"Saved {len(frame):,} hourly regional averages to data/weather/{args.region}_{args.year}.csv")
