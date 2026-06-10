"""Track a single flight live via adsb.lol → MongoDB Landing Zone

Queries adsb.lol by callsign (/v2/callsign/<cs>) or ICAO24 hex (/v2/hex/<hex>)
and writes one position document per API call to MongoDB collection
'flight_tracker_raw'.  Unlike adsb_collector, which stores area snapshots,
this collector stores individual position points suitable for drawing a trail.

Works globally — not limited to the Berlin radius.  Designed to run on the VM
as a cron job or a continuous loop alongside adsb_collector.

Note: Some airlines (e.g. Eurowings) do not broadcast the IATA flight number
as ADS-B callsign.  In that case use --hex <icao24> to track by aircraft
registration hex instead.  The flight_number argument annotates the stored
document for display purposes only.

Usage:
    # Single run by callsign (default EWG7755):
    python collectors/flight_tracker.py

    # Track by ICAO24 hex (when callsign lookup returns nothing):
    python collectors/flight_tracker.py --hex 3c5eee --flight EW7755

    # Continuous polling every 30 seconds:
    python collectors/flight_tracker.py --hex 3c5eee --flight EW7755 --interval 30

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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root (for data_connectors)

from data_connectors.mongo import from_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.adsb.lol/v2"
COLLECTION = "flight_tracker_raw"
DEFAULT_CALLSIGN = "EWG7755"


def fetch_by_callsign(callsign: str) -> dict:
    url = f"{BASE_URL}/callsign/{callsign}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_by_hex(hex_id: str) -> dict:
    url = f"{BASE_URL}/hex/{hex_id}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def build_documents(raw: dict, flight_label: str) -> list[dict]:
    """Return one flat position document per matched aircraft."""
    collected_at = datetime.now(timezone.utc).isoformat()
    docs = []
    for ac in raw.get("ac", []):
        lat = ac.get("lat")
        lon = ac.get("lon")
        if lat is None or lon is None:
            continue
        docs.append({
            "collected_at": collected_at,
            "source": "adsb.lol",
            "flight_label": flight_label,
            "hex": ac.get("hex", ""),
            "registration": ac.get("r"),
            "aircraft_type": ac.get("t"),
            "lat": lat,
            "lon": lon,
            "alt_baro": ac.get("alt_baro"),
            "gs": ac.get("gs"),
            "track": ac.get("track"),
            "squawk": ac.get("squawk"),
            "emergency": ac.get("emergency"),
            "seen": ac.get("seen"),
            "raw_ac": ac,
        })
    return docs


def run_once(db, hex_id: str | None, callsign: str | None, flight_label: str) -> int:
    if hex_id:
        raw = fetch_by_hex(hex_id)
        label = hex_id
    else:
        raw = fetch_by_callsign(callsign)
        label = callsign
    docs = build_documents(raw, flight_label)
    if not docs:
        logger.info("No position data for %s (not airborne or not tracked)", label)
        return 0
    for doc in docs:
        _id = db.insert_raw(COLLECTION, doc)
        logger.info(
            "Position stored: flight=%s reg=%s hex=%s lat=%.4f lon=%.4f alt=%s  _id=%s",
            doc["flight_label"], doc["registration"], doc["hex"],
            doc["lat"], doc["lon"], doc["alt_baro"], _id,
        )
    return len(docs)


def run_loop(hex_id: str | None, callsign: str | None, flight_label: str, interval_seconds: int) -> None:
    logger.info(
        "Starting continuous tracking — flight=%s interval=%ds", flight_label, interval_seconds
    )
    with from_env(write=True) as db:
        while True:
            try:
                run_once(db, hex_id, callsign, flight_label)
            except requests.RequestException as exc:
                logger.warning("API request failed: %s — retrying next interval", exc)
            except Exception as exc:
                logger.error("Unexpected error: %s", exc, exc_info=True)
            time.sleep(interval_seconds)


def run_single(hex_id: str | None, callsign: str | None, flight_label: str) -> None:
    logger.info("Single tracking run — flight=%s", flight_label)
    with from_env(write=True) as db:
        count = run_once(db, hex_id, callsign, flight_label)
    logger.info("Done — %d position(s) written to MongoDB collection '%s'", count, COLLECTION)


def main() -> None:
    parser = argparse.ArgumentParser(description="Track a flight → MongoDB")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--callsign",
        metavar="CALLSIGN",
        help=f"ICAO callsign to track (default: {DEFAULT_CALLSIGN})",
    )
    group.add_argument(
        "--hex",
        metavar="ICAO24",
        help="ICAO24 hex code to track (use when callsign lookup returns nothing)",
    )
    parser.add_argument(
        "--flight",
        metavar="LABEL",
        default=None,
        help="Human-readable flight label stored in MongoDB (e.g. EW7755)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        metavar="SECONDS",
        help="Poll continuously every N seconds (0 = single run, default)",
    )
    args = parser.parse_args()

    hex_id = args.hex
    callsign = args.callsign if args.callsign else (None if hex_id else DEFAULT_CALLSIGN)
    flight_label = args.flight or hex_id or callsign

    if args.interval > 0:
        run_loop(hex_id=hex_id, callsign=callsign, flight_label=flight_label, interval_seconds=args.interval)
    else:
        run_single(hex_id=hex_id, callsign=callsign, flight_label=flight_label)


if __name__ == "__main__":
    main()
