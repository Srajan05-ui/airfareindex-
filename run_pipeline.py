# -*- coding: utf-8 -*-
"""
Single-execution script for GitHub Actions.
Runs the entire data collection and processing pipeline once, then exits.
"""
import sys
from logging_setup import setup_logging

from collector_tier0_dgca import run_once as run_tier0
from collector_tier1 import run_once as run_tier1
from collector_tier2_airline import run_once as run_tier2
from cleaning import run_once as run_cleaning
from index_calc import run_once as run_index_calc
from anomaly import run_once as run_anomaly

logger = setup_logging("sih26056.pipeline")

def main():
    logger.info("=" * 60)
    logger.info("=== Starting automated pipeline run (GitHub Actions) ===")
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

    logger.info("=== Pipeline run completed successfully ===")
    sys.exit(0)

if __name__ == "__main__":
    main()
