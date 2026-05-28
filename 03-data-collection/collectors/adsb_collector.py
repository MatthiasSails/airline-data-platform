"""Collect live ADS-B positions over the Berlin region from adsb.lol → MongoDB Landing Zone

Query: lat/lon radius (Tegel/BER centroid, 60 nm covers all Berlin-area traffic).
One document per API call is written to MongoDB collection 'adsb_raw'.

Usage:
    # Single run (default):
    python collectors/adsb_collector.py

    # Continuous polling every N seconds:
    python collectors/adsb_collector.py --interval 60

Environment variables (via .env at project root):
    MONGO_URI_RW — MongoDB Atlas SRV connection string, collector (write access, required)
    MONGO_DB     — database name                                   (default: airline_landing)
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.mongo.connector import from_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.adsb.lol/v2"
COLLECTION = "adsb_raw"

# Berlin centroid — covers BER, Tegel area, and surrounding corridors
QUERY = {"lat": 52.52, "lon": 13.41, "dist": 60}


def fetch_berlin() -> dict:
    url = f"{BASE_URL}/lat/{QUERY['lat']}/lon/{QUERY['lon']}/dist/{QUERY['dist']}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def build_document(raw: dict) -> dict:
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": "adsb.lol",
        "query_type": "lat_lon_dist",
        "query_params": QUERY,
        "api_timestamp_ms": raw.get("now"),
        "total": raw.get("total", 0),
        "ptime_ms": raw.get("ptime"),
        "ac": raw.get("ac", []),
    }


def run_once(db) -> int:
    raw = fetch_berlin()
    doc = build_document(raw)
    _id = db.insert_adsb_snapshot(COLLECTION, doc)
    logger.info("Snapshot stored: _id=%s  aircraft=%d", _id, doc["total"])
    return doc["total"]


def run_loop(interval_seconds: int) -> None:
    logger.info(
        "Starting continuous collection — interval=%ds, query=%s", interval_seconds, QUERY
    )
    with from_env(write=True) as db:
        while True:
            try:
                run_once(db)
            except requests.RequestException as exc:
                logger.warning("API request failed: %s — retrying next interval", exc)
            except Exception as exc:
                logger.error("Unexpected error: %s", exc, exc_info=True)
            time.sleep(interval_seconds)


def run_single() -> None:
    logger.info("Single collection run — query=%s", QUERY)
    with from_env(write=True) as db:
        count = run_once(db)
    logger.info("Done — %d aircraft written to MongoDB collection '%s'", count, COLLECTION)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect ADS-B data → MongoDB")
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        metavar="SECONDS",
        help="Poll continuously every N seconds (0 = single run, default)",
    )
    args = parser.parse_args()

    if args.interval > 0:
        run_loop(args.interval)
    else:
        run_single()


if __name__ == "__main__":
    main()
