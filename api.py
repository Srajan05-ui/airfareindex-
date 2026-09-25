"""
Stage 6 — minimal REST API exposing the latest index values.

Run with:
    uvicorn api:app --reload --port 8000

Then:
    curl http://localhost:8000/index/latest
or open http://localhost:8000/docs for the interactive Swagger UI --
useful in a demo since a judge can hit "Try it out" themselves.

No auth layer. This is a documented non-goal for the hackathon prototype
(see docs/PRD_hackathon_prototype.md §5) -- a real MoSPI integration
would need one before touching production data.
"""
from datetime import datetime

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from db import get_engine

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AirPrice India — Index API (prototype)",
    description="SIH26056 internal hackathon prototype. Not production-hardened.",
)

import os
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
origins = cors_origins_env.split(",") if cors_origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import RedirectResponse

@app.get("/")
def read_root():
    """Redirect root to the API docs."""
    return RedirectResponse(url="/docs")
@app.on_event("startup")
def create_tables():
    """Auto-create and auto-migrate tables on first boot."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Create airfare_index table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS airfare_index (
                    id SERIAL PRIMARY KEY,
                    origin VARCHAR(10) NOT NULL,
                    destination VARCHAR(10) NOT NULL,
                    base_period VARCHAR(20) DEFAULT '2024-Q1',
                    index_value FLOAT NOT NULL,
                    n_observations INTEGER DEFAULT 0,
                    computed_at_utc TIMESTAMP DEFAULT NOW()
                )
            """))
            # Create fare_observations_clean table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS fare_observations_clean (
                    id SERIAL PRIMARY KEY,
                    airline VARCHAR(100),
                    origin VARCHAR(10),
                    destination VARCHAR(10),
                    price FLOAT,
                    observed_at_utc TIMESTAMP DEFAULT NOW(),
                    is_duplicate BOOLEAN DEFAULT FALSE,
                    is_outlier BOOLEAN DEFAULT FALSE
                )
            """))
            # Auto-add missing base_period column if table already existed without it
            conn.execute(text("""
                DO $$ BEGIN
                    ALTER TABLE airfare_index ADD COLUMN IF NOT EXISTS base_period VARCHAR(20) DEFAULT '2024-Q1';
                EXCEPTION WHEN others THEN NULL;
                END $$;
            """))
            
            # Automatically seed airfare_index if table is empty
            index_count = conn.execute(text("SELECT COUNT(*) FROM airfare_index")).scalar()
            if index_count == 0:
                print("Seeding missing airfare_index data automatically...")
                index_seed = [
                    ("DEL", "BOM", "2024-Q1", 115.2, 420),
                    ("BOM", "BLR", "2024-Q1", 98.4, 380),
                    ("DEL", "BLR", "2024-Q1", 106.1, 510),
                    ("BLR", "CCU", "2024-Q1", 92.5, 290),
                    ("DEL", "CCU", "2024-Q1", 101.0, 440),
                    ("HYD", "MAA", "2024-Q1", 108.9, 310)
                ]
                for r in index_seed:
                    conn.execute(text("""
                        INSERT INTO airfare_index (origin, destination, base_period, index_value, n_observations)
                        VALUES (:origin, :destination, :base_period, :index_value, :n_observations)
                    """), {"origin": r[0], "destination": r[1], "base_period": r[2], "index_value": r[3], "n_observations": r[4]})

            # Automatically seed fare observations if table is missing substantial data
            fares_count = conn.execute(text("""
                SELECT COUNT(*) FROM fare_observations_clean 
                WHERE (is_duplicate = FALSE OR is_duplicate IS NULL) 
                  AND (is_outlier = FALSE OR is_outlier IS NULL) 
                  AND price IS NOT NULL
            """)).scalar()
            if fares_count < 5:
                print("Seeding missing fare_observations_clean data automatically...")
                fares_seed = [
                    ('IndiGo', 'DEL', 'BOM', 5200),
                    ('Air India', 'DEL', 'BOM', 6100),
                    ('SpiceJet', 'BOM', 'BLR', 4700),
                    ('IndiGo', 'BOM', 'BLR', 5100),
                    ('Vistara', 'DEL', 'BLR', 7200),
                    ('IndiGo', 'DEL', 'BLR', 5400),
                    ('Air India', 'DEL', 'CCU', 6500),
                    ('IndiGo', 'DEL', 'CCU', 5600),
                    ('SpiceJet', 'HYD', 'MAA', 4200),
                    ('IndiGo', 'HYD', 'MAA', 4900)
                ]
                for f in fares_seed:
                    conn.execute(text("""
                        INSERT INTO fare_observations_clean (airline, origin, destination, price, is_duplicate, is_outlier)
                        VALUES (:airline, :origin, :destination, :price, FALSE, FALSE)
                    """), {"airline": f[0], "origin": f[1], "destination": f[2], "price": f[3]})

            conn.commit()
            print("Tables created/verified OK.")
    except Exception as e:
        print(f"Startup table setup warning: {e}")

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from run_pipeline import main as run_pipeline_main
        from datetime import datetime, timedelta
        
        # Start the automated daily scraping pipeline in the background
        scheduler = BackgroundScheduler()
        # Schedule to run every 24 hours (or adjust as needed)
        scheduler.add_job(run_pipeline_main, 'interval', hours=24, id='daily_scraper', replace_existing=True)
        scheduler.start()
        print("Smart Automation: Background web scraping pipeline scheduled successfully.")
        
        # Optionally, kick off the first run 1 minute after boot
        scheduler.add_job(run_pipeline_main, 'date', run_date=datetime.now() + timedelta(minutes=1), id='initial_scraper')
    except Exception as e:
        print(f"Smart Automation warning - failed to schedule pipeline: {e}")

class IndexPoint(BaseModel):
    origin: str
    destination: str
    base_period: str
    index_value: float
    n_observations: int
    computed_at_utc: datetime

@app.get("/force-seed")
def force_seed():
    """Manually force seed the database to fix empty data issues."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            fares_seed = [
                ('IndiGo', 'DEL', 'BOM', 5200),
                ('Air India', 'DEL', 'BOM', 6100),
                ('SpiceJet', 'BOM', 'BLR', 4700),
                ('IndiGo', 'BOM', 'BLR', 5100),
                ('Vistara', 'DEL', 'BLR', 7200),
                ('IndiGo', 'DEL', 'BLR', 5400),
                ('Air India', 'DEL', 'CCU', 6500),
                ('IndiGo', 'DEL', 'CCU', 5600),
                ('SpiceJet', 'HYD', 'MAA', 4200),
                ('IndiGo', 'HYD', 'MAA', 4900)
            ]
            for f in fares_seed:
                conn.execute(text("""
                    INSERT INTO fare_observations_clean (airline, origin, destination, price, is_duplicate, is_outlier)
                    VALUES (:airline, :origin, :destination, :price, FALSE, FALSE)
                """), {"airline": f[0], "origin": f[1], "destination": f[2], "price": f[3]})
            return {"status": "success", "message": "Fares seeded successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health")
def health_check():
    """Lightweight endpoint for UptimeRobot to keep the Render server awake."""
    return {"status": "ok", "service": "airfare-api"}

@app.post("/seed")
def seed_sample_data():
    """Seed the database with sample data for testing. Call once after deployment."""
    engine = get_engine()
    sample_index = [
        ("DEL", "BOM", "2024-Q1", 115.2, 420),
        ("BOM", "BLR", "2024-Q1", 98.4, 380),
        ("DEL", "BLR", "2024-Q1", 106.1, 510),
        ("BLR", "CCU", "2024-Q1", 92.5, 290),
        ("DEL", "CCU", "2024-Q1", 101.0, 440),
        ("HYD", "MAA", "2024-Q1", 108.9, 310),
        ("DEL", "HYD", "2024-Q1", 103.5, 395),
        ("BOM", "COK", "2024-Q1", 97.2, 265),
        ("DEL", "GOI", "2024-Q1", 111.8, 345),
        ("AMD", "BOM", "2024-Q1", 94.1, 220),
    ]
    sample_fares = [
        ("IndiGo", "DEL", "BOM", 5200),
        ("Air India", "DEL", "BOM", 6100),
        ("SpiceJet", "BOM", "BLR", 4700),
        ("IndiGo", "BOM", "BLR", 5100),
        ("Vistara", "DEL", "BLR", 7200),
        ("IndiGo", "DEL", "BLR", 5400),
        ("Air India", "DEL", "CCU", 6500),
        ("IndiGo", "DEL", "CCU", 5600),
        ("SpiceJet", "HYD", "MAA", 4200),
        ("IndiGo", "HYD", "MAA", 4900),
    ]
    try:
        with engine.connect() as conn:
            # Insert index data
            for row in sample_index:
                conn.execute(text("""
                    INSERT INTO airfare_index (origin, destination, base_period, index_value, n_observations)
                    VALUES (:origin, :destination, :base_period, :index_value, :n_observations)
                    ON CONFLICT DO NOTHING
                """), {"origin": row[0], "destination": row[1], "base_period": row[2],
                       "index_value": row[3], "n_observations": row[4]})
            # Insert fare observations
            for row in sample_fares:
                conn.execute(text("""
                    INSERT INTO fare_observations_clean (airline, origin, destination, price)
                    VALUES (:airline, :origin, :destination, :price)
                """), {"airline": row[0], "origin": row[1], "destination": row[2], "price": row[3]})
            conn.commit()
        return {"status": "seeded", "index_rows": len(sample_index), "fare_rows": len(sample_fares)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/index/latest", response_model=list[IndexPoint])
def latest_index():
    engine = get_engine()
    try:
        df = pd.read_sql(
            text(
                """
                SELECT origin, destination, base_period, index_value,
                    n_observations, computed_at_utc
                FROM airfare_index
                ORDER BY origin, destination, computed_at_utc DESC
                """
            ),
            engine,
        )
    except Exception as e:
        print(f"Database error (tables might not exist yet): {e}")
        return []

    if df.empty:
        return []
    df = df.drop_duplicates(subset=["origin", "destination"], keep="first")
    if df.empty:
        return []
    df["base_period"] = df["base_period"].astype(str)
    return df.to_dict(orient="records")


@app.get("/fares/latest")
def latest_fares():
    engine = get_engine()
    try:
        df = pd.read_sql(
            text(
                """
                SELECT airline, origin, destination, price, observed_at_utc, is_duplicate, is_outlier
                FROM fare_observations_clean
                WHERE (is_duplicate = FALSE OR is_duplicate IS NULL) 
                  AND (is_outlier = FALSE OR is_outlier IS NULL) 
                  AND price IS NOT NULL
                ORDER BY observed_at_utc DESC
                LIMIT 5000
                """
            ),
            engine,
        )
    except Exception as e:
        print(f"Database error (tables might not exist yet): {e}")
        return []
        
    if df.empty:
        return []
    return df.to_dict(orient="records")



@app.get("/mock-airline/search")
def mock_airline_search(origin: str, destination: str, date: str):
    """
    Returns a complex, deeply nested JSON response simulating a real airline's internal API.
    """
    import random
    
    # Generate somewhat realistic, random fares based on route
    base_fare = 5000 if origin == "BOM" or destination == "BOM" else 7000
    base_fare += random.randint(-1000, 2000)
    
    # Simulating a complex JSON payload typical of airline backends (e.g. Navitaire / Amadeus)
    return {
        "status": "success",
        "data": {
            "searchCriteria": {
                "origin": origin,
                "destination": destination,
                "departureDate": date
            },
            "flightResults": {
                "journeys": [
                    {
                        "journeyId": f"JNY-{random.randint(1000,9999)}",
                        "segments": [
                            {
                                "flightDesignator": {
                                    "carrierCode": "6E",
                                    "flightNumber": f"{random.randint(100, 999)}"
                                },
                                "origin": origin,
                                "destination": destination,
                                "departureTime": f"{date}T08:00:00",
                                "arrivalTime": f"{date}T10:30:00"
                            }
                        ],
                        "fares": {
                            "ECONOMY": {
                                "totalAmount": base_fare,
                                "currency": "INR",
                                "taxBreakdown": {
                                    "base": base_fare * 0.8,
                                    "taxes": base_fare * 0.2
                                }
                            },
                            "BUSINESS": {
                                "totalAmount": base_fare * 3.5,
                                "currency": "INR",
                                "taxBreakdown": {
                                    "base": base_fare * 3.5 * 0.8,
                                    "taxes": base_fare * 3.5 * 0.2
                                }
                            }
                        }
                    },
                    {
                        "journeyId": f"JNY-{random.randint(1000,9999)}",
                        "segments": [
                            {
                                "flightDesignator": {
                                    "carrierCode": "6E",
                                    "flightNumber": f"{random.randint(100, 999)}"
                                },
                                "origin": origin,
                                "destination": destination,
                                "departureTime": f"{date}T15:00:00",
                                "arrivalTime": f"{date}T17:30:00"
                            }
                        ],
                        "fares": {
                            "ECONOMY": {
                                "totalAmount": base_fare + 450,
                                "currency": "INR",
                                "taxBreakdown": {
                                    "base": (base_fare + 450) * 0.8,
                                    "taxes": (base_fare + 450) * 0.2
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
