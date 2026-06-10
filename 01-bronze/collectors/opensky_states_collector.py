"""Collect live state vectors from OpenSky /states/all → MongoDB Landing Zone

One document per API call is written to MongoDB collection 'opensky_raw'.
Uses OAuth2 credentials when available; falls back to unauthenticated
(rate-limited: 1 req / 10 s, max 400 results) if credentials are absent.

See ADR 009: /states/all is the Silver-layer source; /flights/* is retired.

Usage:
    # Single run (default):
    python collectors/opensky_states_collector.py

    # Continuous polling every N seconds:
    python collectors/opensky_states_collector.py --interval 60

Environment variables (via .env at project root):
    OPENSKY_CLIENT_ID      — OAuth2 client ID        (optional, improves rate limits)
    OPENSKY_CLIENT_SECRET  — OAuth2 client secret    (optional)
    MONGO_URI_RW           — MongoDB Atlas SRV connection string (write access, required)
    MONGO_DB               — database name            (default: airline_landing)
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root (for data_connectors)

from data_connectors.mongo import from_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

COLLECTION = "opensky_raw"
STATES_URL = "https://opensky-network.org/api/states/all"

# Bounding box: Frankfurt ~150x150 km (centre 50.11°N 8.68°E, ±75 km)
BBOX = {"lamin": 49.43, "lomin": 7.63, "lamax": 50.79, "lomax": 9.73}


def _auth() -> HTTPBasicAuth | None:
    import os
    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
    if client_id and client_secret:
        return HTTPBasicAuth(client_id, client_secret)
    return None


def fetch_states() -> dict:
    response = requests.get(
        STATES_URL,
        params=BBOX,
        auth=_auth(),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def build_document(raw: dict) -> dict:
    return {
        "collected_at":  datetime.now(timezone.utc).isoformat(),
        "source":        "opensky-network",
        "endpoint":      "/states/all",
        "query_params":  BBOX,
        "api_timestamp": raw.get("time"),
        "state_count":   len(raw.get("states") or []),
        "states":        raw.get("states") or [],
    }


def run_once(db) -> int:
    raw = fetch_states()
    doc = build_document(raw)
    _id = db.insert_raw(COLLECTION, doc)
    logger.info(
        "Snapshot stored: _id=%s  states=%d  api_ts=%s",
        _id, doc["state_count"], doc["api_timestamp"],
    )
    return doc["state_count"]


def run_loop(interval_seconds: int) -> None:
    logger.info("Starting continuous collection — interval=%ds, bbox=%s", interval_seconds, BBOX)
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
    logger.info("Single collection run — bbox=%s", BBOX)
    with from_env(write=True) as db:
        count = run_once(db)
    logger.info("Done — %d states written to MongoDB collection '%s'", count, COLLECTION)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect OpenSky /states/all → MongoDB")
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
