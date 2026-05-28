"""Collect structured flight data from OpenSky Network API → MongoDB Landing Zone

Queries departures and arrivals for Berlin BER (EDDB) over a configurable look-back window.
One document per API call is written to MongoDB collection 'opensky_raw'.

IMPORTANT: Must run locally — OpenSky auth (auth.opensky-network.org) is blocked from Liora VM.
See ADR 004 and ADR 005.

Usage:
    # Single run (default: last 24 hours, live API):
    python collectors/opensky_collector.py

    # Custom time window:
    python collectors/opensky_collector.py --hours 6

    # Mock mode (no credentials needed):
    python collectors/opensky_collector.py --mock

Environment variables (via .env at project root):
    OPENSKY_CLIENT_ID      — OAuth2 client ID
    OPENSKY_CLIENT_SECRET  — OAuth2 client secret
    MONGO_URI              — MongoDB Atlas SRV connection string  (required)
    MONGO_DB               — database name                        (default: airline_landing)
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.mongo.connector import from_env
from opensky_api.client import OpenSkyClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

COLLECTION = "opensky_raw"
DEFAULT_AIRPORT = "EDDB"
DEFAULT_LOOK_BACK_HOURS = 24


def build_document(endpoint: str, airport: str, begin: int, end: int, flights: list) -> dict:
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": "opensky-network",
        "endpoint": endpoint,
        "query_params": {"airport": airport, "begin": begin, "end": end},
        "flight_count": len(flights),
        "flights": flights,
    }


def run_once(db, client: OpenSkyClient, airport: str, look_back_hours: int) -> None:
    end = int(time.time())
    begin = end - look_back_hours * 3600

    logger.info("Querying %s  window=%dh  begin=%d  end=%d", airport, look_back_hours, begin, end)

    for endpoint_name, fetch_fn in [
        ("departures", client.get_departures),
        ("arrivals", client.get_arrivals),
    ]:
        flights = fetch_fn(airport, begin, end)
        doc = build_document(endpoint_name, airport, begin, end, flights)
        _id = db.insert_raw(COLLECTION, doc)
        logger.info("%-12s  flights=%3d  _id=%s", endpoint_name, doc["flight_count"], _id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect OpenSky flight data → MongoDB")
    parser.add_argument(
        "--airport",
        default=DEFAULT_AIRPORT,
        help=f"ICAO airport code (default: {DEFAULT_AIRPORT})",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_LOOK_BACK_HOURS,
        metavar="N",
        help=f"Look-back window in hours (default: {DEFAULT_LOOK_BACK_HOURS})",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of live API (no credentials needed)",
    )
    args = parser.parse_args()

    client = OpenSkyClient(use_mock=args.mock)
    mode = "MOCK" if args.mock else "LIVE"
    logger.info(
        "Starting OpenSky collector  airport=%s  hours=%d  mode=%s",
        args.airport, args.hours, mode,
    )

    with from_env() as db:
        run_once(db, client, args.airport, args.hours)

    logger.info("Done — documents written to MongoDB collection '%s'", COLLECTION)


if __name__ == "__main__":
    main()
