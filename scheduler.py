import time
import schedule
import logging
from logging_setup import setup_logging

from collector_tier0_dgca import run_once as run_tier0
from collector_tier1 import run_once as run_tier1
from collector_tier2_airline import run_once as run_tier2
from cleaning import run_once as run_cleaning
from index_calc import run_once as run_index_calc
from anomaly import run_once as run_anomaly

logger = setup_logging("sih26056.scheduler")

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE: Twice daily — 06:00 IST (morning) and 18:00 IST (evening)
# ─────────────────────────────────────────────────────────────────────────────
SCHEDULE_TIMES = ["06:00", "18:00"]

def job():
    logger.info("=" * 60)
    logger.info("=== Starting scheduled pipeline run ===")
    logger.info("=" * 60)

    try:
        logger.info("[1/6] Running Tier 0 (DGCA)...")
        run_tier0()
        logger.info("[1/6] Tier 0 — DONE")
    except Exception as e:
        logger.error(f"[1/6] Tier 0 FAILED: {e}")

    try:
        logger.info("[2/6] Running Tier 1 (Google Flights)...")
        run_tier1()
        logger.info("[2/6] Tier 1 — DONE")
    except Exception as e:
        logger.error(f"[2/6] Tier 1 FAILED: {e}")

    try:
        logger.info("[3/6] Running Tier 2 (Airline websites)...")
        run_tier2()
        logger.info("[3/6] Tier 2 — DONE")
    except Exception as e:
        logger.error(f"[3/6] Tier 2 FAILED: {e}")

    try:
        logger.info("[4/6] Running Cleaning & Deduplication...")
        run_cleaning()
        logger.info("[4/6] Cleaning — DONE")
    except Exception as e:
        logger.error(f"[4/6] Cleaning FAILED: {e}")

    try:
        logger.info("[5/6] Running Index Calculation (CPI)...")
        run_index_calc()
        logger.info("[5/6] Index Calculation — DONE")
    except Exception as e:
        logger.error(f"[5/6] Index Calculation FAILED: {e}")

    try:
        logger.info("[6/6] Running Anomaly Detection...")
        run_anomaly()
        logger.info("[6/6] Anomaly Detection — DONE")
    except Exception as e:
        logger.error(f"[6/6] Anomaly Detection FAILED: {e}")

    logger.info("=== Completed scheduled pipeline run ===")
    logger.info(f"    Next runs scheduled at: {SCHEDULE_TIMES}")
    logger.info("=" * 60)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AirPrice India — Data Pipeline Scheduler STARTED")
    logger.info(f"Schedule: TWICE DAILY at {SCHEDULE_TIMES[0]} and {SCHEDULE_TIMES[1]} (IST)")
    logger.info("=" * 60)

    # Run immediately on startup so data is fresh when the dashboard opens
    logger.info("Running initial pipeline job on startup...")
    job()

    # Schedule twice-daily runs
    for t in SCHEDULE_TIMES:
        schedule.every().day.at(t).do(job)
        logger.info(f"Scheduled daily run at {t} IST")

    logger.info("Entering schedule loop. Waiting for next run...")
    while True:
        schedule.run_pending()
        time.sleep(30)   # check every 30 seconds (fine-grained enough for minute-level schedules)
