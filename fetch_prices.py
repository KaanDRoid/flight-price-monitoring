import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Load the .env file that sits next to this script
load_dotenv(dotenv_path=Path(__file__).parent / '.env')
TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

BASE = "https://api.travelpayouts.com/v2/prices/latest"

ROUTES = [
    ("BCN", "MAD"),    # Barcelona to Madrid
    ("BCN", "FRA"),    # Barcelona to Frankfurt
    ("IST", "BCN"),    # Istanbul to Barcelona
    ("BCN", "IST"),    # Barcelona to Istanbul
    ("ESB", "IST"),    # Ankara to Istanbul
    ("IST", "NRT"),    # Istanbul to Tokyo
    ("BCN", "LAX"),    # Barcelona to Los Angeles
    ("IST", "EZE"),    # Istanbul to Buenos Aires
    ("ESB", "LAX"),    # Ankara to Los Angeles
    ("NRT", "EZE"),    # Tokyo to Buenos Aires
]


def fetch_route(origin, destination):
    params = {
        "currency": "eur",
        "origin": origin,
        "destination": destination,
        "show_to_affiliates": "true",
        "sorting": "price",
        "limit": 30
    }
    try:
        resp = requests.get(BASE, headers={"x-access-token": TOKEN}, params=params, timeout=30)
        resp.raise_for_status()
        try:
            data = resp.json()["data"]
        except Exception as e:
            print(f"JSON decode error for {origin}-{destination}: {e}\nResponse: {resp.text}")
            return pd.DataFrame()
        df = pd.json_normalize(data)
        if not df.empty:
            df = df.rename(columns={"value": "price_eur"})
        return df
    except Exception as e:
        print(f"API error for {origin}-{destination}: {e}")
        return pd.DataFrame()


def main():
    if not TOKEN:
        sys.exit("TRAVELPAYOUTS_TOKEN is not set. Add it to a .env file next to this script.")

    # The collection date is used as the snapshot folder name
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y%m%d")

    print(f"Starting flight price collection - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Create snapshot directory structure
    snapshot_dir = Path("snapshots") / date_str
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    route_breakdown_dir = snapshot_dir / "route_breakdown"
    route_breakdown_dir.mkdir(exist_ok=True)

    all_dfs = []
    print(f"\nFetching data for {len(ROUTES)} routes...")

    for i, (origin, destination) in enumerate(ROUTES, 1):
        print(f"   {i:2d}/{len(ROUTES)}: {origin} -> {destination}", end=" ... ")
        df = fetch_route(origin, destination)
        if not df.empty:
            all_dfs.append(df)
            # Save individual route data to the snapshot directory
            route_file = route_breakdown_dir / f"{origin.lower()}_{destination.lower()}_prices.csv"
            df.to_csv(route_file, index=False)
            print(f"{len(df)} flights found")
        else:
            print("no data")

    if not all_dfs:
        print("No data found for any route.")
        return

    df_all = pd.concat(all_dfs, ignore_index=True)

    # Add metadata
    df_all['collection_timestamp'] = timestamp.isoformat()
    df_all['snapshot_date'] = date_str

    snapshot_file = snapshot_dir / "all_routes.csv"
    df_all.to_csv(snapshot_file, index=False)

    print("\nData collection completed")
    print(f"Snapshot saved to: {snapshot_dir}")
    print(f"Total flights collected: {len(df_all)}")
    print(f"Departure dates: {df_all['depart_date'].min()} to {df_all['depart_date'].max()}")
    print(f"Price range: EUR {df_all['price_eur'].min()} - {df_all['price_eur'].max()}")
    print(f"Average price: EUR {df_all['price_eur'].mean():.2f}")

    # Cheapest flight per route
    print("\nCheapest flights by route")
    print("-" * 40)
    cheapest = df_all.groupby(['origin', 'destination'])['price_eur'].min().reset_index()
    cheapest['route'] = cheapest['origin'] + ' -> ' + cheapest['destination']
    for _, row in cheapest.sort_values('price_eur').iterrows():
        print(f"   {row['route']}: EUR {row['price_eur']}")

    # Number of offers per OTA
    print("\nOTA distribution")
    print("-" * 20)
    for ota, count in df_all['gate'].value_counts().items():
        print(f"   {ota}: {count} flights")

    print("\nFirst 5 records from this snapshot:")
    print(df_all[['origin', 'destination', 'depart_date', 'price_eur', 'gate']].head())

    summary = {
        'collection_timestamp': timestamp.isoformat(),
        'snapshot_date': date_str,
        'total_flights': len(df_all),
        'routes_covered': len(ROUTES),
        'active_otas': df_all['gate'].nunique(),
        'price_range_min': float(df_all['price_eur'].min()),
        'price_range_max': float(df_all['price_eur'].max()),
        'average_price': float(df_all['price_eur'].mean()),
        'date_range_start': df_all['depart_date'].min(),
        'date_range_end': df_all['depart_date'].max()
    }

    summary_file = snapshot_dir / "snapshot_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSnapshot summary saved: {summary_file}")
    print("\nTo compare with a later snapshot run:")
    print(f"   python price_comparison_analysis.py --date1 {date_str} --date2 YYYYMMDD")


if __name__ == "__main__":
    main()
