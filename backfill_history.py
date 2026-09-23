from datetime import datetime, timedelta, timezone
import random
import pandas as pd
from sqlalchemy import text
from db import get_engine

engine = get_engine()

def backfill():
    routes = [
        ("DEL", "BOM", 5000), ("BOM", "BLR", 4000), ("DEL", "BLR", 6000),
        ("DEL", "CCU", 5500), ("BOM", "CCU", 6500), ("BLR", "HYD", 3500),
        ("DEL", "HYD", 5000), ("DEL", "MAA", 7000), ("BOM", "MAA", 4500)
    ]
    
    # 14 days ago
    past_date = datetime.now(timezone.utc) - timedelta(days=14)
    
    rows = []
    for origin, dest, base_fare in routes:
        # Simulate prices that were cheaper 14 days ago to show inflation today
        past_price = base_fare * random.uniform(0.7, 0.9)  # 10-30% cheaper in the past
        
        rows.append({
            "observed_at_utc": past_date,
            "source_tier": "tier1_mock_history",
            "source_detail": "historical_backfill",
            "origin": origin,
            "destination": dest,
            "departure_date": (past_date + timedelta(days=15)).date().isoformat(),
            "booking_window_days": 15,
            "airline": "MOCK",
            "fare_type": "economy",
            "price": past_price,
            "currency": "INR",
            "is_price_band": False,
            "is_duplicate": False,
            "is_outlier": False,
            "raw_ref": "mock_history"
        })
        
    df = pd.DataFrame(rows)
    df.to_sql("fare_observations_clean", engine, if_exists="append", index=False)
    print(f"Backfilled {len(df)} historical clean records.")

if __name__ == "__main__":
    backfill()
