import logging
from pymongo import MongoClient
import pandas as pd
from pprint import pprint
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

col_names = ["icao24", "callsign", "time_position", "longitude", "latitude", "on_ground", "true_track", "vertical_rate"]
cols = [0, 1, 3, 5, 6, 8, 10, 11]


def map_opensky_doc(doc):
    """OpenSky /states/all snapshot → map1 rows (positional state-vector columns)."""
    return [[state[i] for i in cols] for state in doc["states"]]


def map_adsb_doc(doc):
    """adsb.lol snapshot → map1 rows. Fallback source for when OpenSky is unreachable
    (e.g. the AWS VM's egress IP is blocked by OpenSky)."""
    now_ms = doc.get("now")
    rows = []
    for ac in doc.get("ac", []):
        lat, lon = ac.get("lat"), ac.get("lon")
        if lat is None or lon is None:
            continue  # no position fix yet — nothing to map

        alt_baro = ac.get("alt_baro")
        seen_pos = ac.get("seen_pos")
        time_position = int(now_ms / 1000 - seen_pos) if now_ms is not None and seen_pos is not None else None

        rows.append([
            ac.get("hex"),                                   # icao24
            (ac.get("flight") or "").strip() or None,         # callsign
            time_position,
            lon,                                              # longitude
            lat,                                              # latitude
            alt_baro == "ground",                              # on_ground
            ac.get("track"),                                  # true_track
            ac.get("baro_rate", ac.get("geom_rate")),          # vertical_rate
        ])
    return rows


try:
    client = MongoClient(os.environ["MONGO_URL"])
    db = client["airlines"]
    opensky_doc = db["states_all"].find_one({}, sort=[("fetched_at", -1)])
    adsb_doc = db["adsb_raw"].find_one({}, sort=[("fetched_at", -1)])

    # Freshest snapshot wins — on the VM, OpenSky calls fail silently (egress
    # blocked) so its snapshot goes stale while adsb_raw keeps updating.
    use_adsb = adsb_doc is not None and (
        opensky_doc is None or adsb_doc["fetched_at"] > opensky_doc["fetched_at"]
    )

    if use_adsb:
        log.info(f"Using adsb.lol fallback (fetched_at={adsb_doc['fetched_at']}) — fresher than OpenSky snapshot.")
        rows = map_adsb_doc(adsb_doc)
    else:
        log.info(f"Using OpenSky snapshot (fetched_at={opensky_doc['fetched_at']}).")
        rows = map_opensky_doc(opensky_doc)

    log.info(f"Fetched {len(rows)} rows from MongoDB.")
except KeyError as e:
    log.error(f"Missing environment variable: {e}")
    raise
except Exception as e:
    log.error(f"Failed to fetch data from MongoDB: {e}")
    raise

try:
    conn = psycopg2.connect(
        host=os.environ["SUPABASE_DB_URL"],
        port=5432,
        database="postgres",
        user="postgres",  # Direct Connection (port 5432) — not the Supavisor pooler user format
        password=os.environ["SUPABASE_DB_PASSWORD"]
    )
    cur = conn.cursor()
    cur.execute("DELETE FROM map1")
    execute_values(cur,
        "INSERT INTO map1 (icao24, callsign, time_position, longitude, latitude, on_ground, true_track, vertical_rate, created_at) VALUES %s",
        [[*row, datetime.now(timezone.utc)] for row in rows]
    )
    conn.commit()
    cur.close()
    conn.close()
    log.info(f"Written {len(rows)} rows to PostgreSQL.")
except KeyError as e:
    log.error(f"Missing environment variable: {e}")
    raise
except Exception as e:
    log.error(f"Failed to write to PostgreSQL: {e}")
    raise

