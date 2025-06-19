import os
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Explicitly load the .env file from the script's directory
load_dotenv(dotenv_path=Path(__file__).parent / '.env')
TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

BASE = "https://api.travelpayouts.com/v2/prices/latest"


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
        resp = requests.get(BASE, headers={"x-access-token": TOKEN}, params=params)
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
    # Get current timestamp for snapshot organization
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y%m%d")
    time_str = timestamp.strftime("%H%M%S")
    
    print(f"🚀 Starting flight price collection - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create snapshot directory structure
    snapshot_dir = Path("snapshots") / date_str
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    route_breakdown_dir = snapshot_dir / "route_breakdown"
    route_breakdown_dir.mkdir(exist_ok=True)
    
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
        ("NRT", "EZE")     # Tokyo to Buenos Aires
    ]
    
    all_dfs = []
    print(f"\n📊 Fetching data for {len(ROUTES)} routes...")
    
    for i, (origin, destination) in enumerate(ROUTES, 1):
        print(f"   {i:2d}/10: {origin} → {destination}", end=" ... ")
        df = fetch_route(origin, destination)
        if not df.empty:
            all_dfs.append(df)
            # Save individual route data to snapshot directory
            route_file = route_breakdown_dir / f"{origin.lower()}_{destination.lower()}_prices.csv"
            df.to_csv(route_file, index=False)
            print(f"✅ {len(df)} flights found")
        else:
            print("❌ No data")
    
    if all_dfs:
        df_all = pd.concat(all_dfs, ignore_index=True)
        
        # Add metadata
        df_all['collection_timestamp'] = timestamp.isoformat()
        df_all['snapshot_date'] = date_str
          # Save to snapshot directory
        snapshot_file = snapshot_dir / "all_routes.csv"
        df_all.to_csv(snapshot_file, index=False)
        
        print(f"\n✅ DATA COLLECTION COMPLETED")
        print(f"📁 Snapshot saved to: {snapshot_dir}")
        print(f"📊 Total flights collected: {len(df_all)}")
        print(f"📅 Date range: {df_all['depart_date'].min()} to {df_all['depart_date'].max()}")
        print(f"💰 Price range: €{df_all['price_eur'].min()} - €{df_all['price_eur'].max()}")
        print(f"💵 Average price: €{df_all['price_eur'].mean():.2f}")
        
        # Show cheapest flights by route
        print(f"\n🏆 CHEAPEST FLIGHTS BY ROUTE")
        print("-" * 40)
        cheapest = df_all.groupby(['origin', 'destination'])['price_eur'].min().reset_index()
        cheapest['route'] = cheapest['origin'] + ' → ' + cheapest['destination']
        cheapest_sorted = cheapest.sort_values('price_eur')
        for _, row in cheapest_sorted.iterrows():
            print(f"   {row['route']}: €{row['price_eur']}")
        
        # Show OTA distribution
        print(f"\n🏢 OTA DISTRIBUTION")
        print("-" * 20)
        ota_counts = df_all['gate'].value_counts()
        for ota, count in ota_counts.items():
            print(f"   {ota}: {count} flights")
            
        print(f"\n📈 First 5 records from this snapshot:")
        print(df_all[['origin', 'destination', 'depart_date', 'price_eur', 'gate']].head())
        
        # Create a snapshot summary
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
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Snapshot summary saved: {summary_file}")
        
    else:
        print("❌ No data found for any route.")
        
    print(f"\n🎯 Next steps:")
    print(f"   • Run again tomorrow to create comparison data")
    print(f"   • Use: python price_comparison_analysis.py --date1 {date_str} --date2 YYYYMMDD")
    print(f"   • Analyze trends with the time series data")


if __name__ == "__main__":
    main()
