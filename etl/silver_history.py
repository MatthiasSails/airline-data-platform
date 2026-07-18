"""
silver_history.py — Incremental, idempotent, watermarked Silver/Gold loader (Redshift).

Parallel to etl/silver.py (which full-refreshes the map1 live-map table on Supabase and is
left untouched). This loader instead ACCUMULATES history in Redshift:

    MongoDB Bronze (adsb_raw)
        -> read only documents newer than the stored watermark (fetched_at)
        -> map to position rows, deterministic obs_id = md5(icao24 | time_position)
        -> bulk-load into a session TEMP table
        -> run etl/sql/load_incremental.sql (insert-if-new into silver + gold, sessionize legs)
        -> advance the watermark (only after success)

Idempotency: re-running over the same Bronze is a no-op — deterministic obs_id + insert-if-new
means already-loaded observations are never duplicated. Watermark is advanced last, so a crash
mid-run just replays a safe window on the next run. See ADR 020 / 021 / 022.

adsb.lol only — registration/type come from adsb `r`/`t`; no OpenSky, no reference data, no S3.

Redshift is Postgres-wire-compatible, so we connect with psycopg2 (ADR 002), same as silver.py.
Credentials come from .env for now; runtime secrets move to Secrets Manager with the Terraform
work (ADR 020, deferred).
"""
import os
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, errors as mongo_errors
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# =============================================================================
# CONFIG
# =============================================================================
SQL_DIR         = Path(__file__).parent / "sql"
LOAD_SQL        = SQL_DIR / "load_incremental.sql"
WATERMARK_KEY   = "silver.aircraft_position"   # row identifier in meta.etl_watermark
EPOCH_ISO       = "1970-01-01T00:00:00+00:00"
FLIGHT_WATERMARK = None  # legs are recomputed from a rolling window, not watermarked separately

# Columns loaded into the staging temp table, in order.
STAGING_COLS = [
    "obs_id", "icao24", "callsign", "time_position", "event_date",
    "longitude", "latitude", "on_ground", "true_track", "vertical_rate",
    "alt_baro", "ground_speed", "registration", "type_code", "source", "loaded_at",
]


# =============================================================================
# CONNECTIONS
# =============================================================================
def get_mongo_db():
    """Connect to MongoDB Atlas and return the airlines database."""
    try:
        client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        log.info("MongoDB connection established.")
        return client["airlines"]
    except KeyError:
        log.error("MONGO_URL not set. Ensure it is defined in .env")
        raise
    except mongo_errors.ServerSelectionTimeoutError as e:
        log.error(f"Could not connect to MongoDB: {e}")
        raise


def get_redshift_conn():
    """Connect to Redshift (Postgres-wire-compatible) via psycopg2."""
    try:
        return psycopg2.connect(
            host=os.environ["REDSHIFT_HOST"],
            port=int(os.environ.get("REDSHIFT_PORT", "5439")),
            dbname=os.environ["REDSHIFT_DB"],
            user=os.environ["REDSHIFT_USER"],
            password=os.environ["REDSHIFT_PASSWORD"],
        )
    except KeyError as e:
        log.error(f"Missing Redshift env var: {e}. Need REDSHIFT_HOST/DB/USER/PASSWORD in .env")
        raise


# =============================================================================
# MAPPING  (mirrors etl/silver.py's map_adsb_doc, plus alt_baro/ground_speed/r/t)
# =============================================================================
def _obs_id(icao24: str, time_position: int) -> str:
    return hashlib.md5(f"{icao24}|{time_position}".encode()).hexdigest()


def map_adsb_doc(doc: dict) -> list[dict]:
    """adsb.lol snapshot document -> list of position rows."""
    now_ms = doc.get("now")
    rows: list[dict] = []
    for ac in doc.get("ac", []):
        lat, lon = ac.get("lat"), ac.get("lon")
        if lat is None or lon is None:
            continue  # no position fix yet

        seen_pos = ac.get("seen_pos")
        time_position = (
            int(now_ms / 1000 - seen_pos)
            if now_ms is not None and seen_pos is not None else None
        )
        icao24 = ac.get("hex")
        if not icao24 or time_position is None:
            continue  # obs_id / event_date require both

        alt_baro = ac.get("alt_baro")
        rows.append({
            "obs_id":        _obs_id(icao24, time_position),
            "icao24":        icao24,
            "callsign":      (ac.get("flight") or "").strip() or None,
            "time_position": time_position,
            "event_date":    datetime.fromtimestamp(time_position, tz=timezone.utc).date(),
            "longitude":     lon,
            "latitude":      lat,
            "on_ground":     alt_baro == "ground",
            "true_track":    ac.get("track"),
            "vertical_rate": ac.get("baro_rate", ac.get("geom_rate")),
            "alt_baro":      alt_baro if isinstance(alt_baro, (int, float)) else None,
            "ground_speed":  ac.get("gs"),
            "registration":  ac.get("r"),
            "type_code":     ac.get("t"),
            "source":        "adsb_raw",
        })
    return rows


# =============================================================================
# WATERMARK
# =============================================================================
def read_watermark(cur) -> str:
    cur.execute(
        "SELECT last_watermark FROM meta.etl_watermark WHERE table_name = %s",
        (WATERMARK_KEY,),
    )
    row = cur.fetchone()
    return row[0] if row else EPOCH_ISO


def advance_watermark(cur, new_watermark: str) -> None:
    cur.execute(
        "UPDATE meta.etl_watermark SET last_watermark = %s, updated_at = SYSDATE "
        "WHERE table_name = %s",
        (new_watermark, WATERMARK_KEY),
    )
    if cur.rowcount == 0:
        cur.execute(
            "INSERT INTO meta.etl_watermark (table_name, last_watermark, updated_at) "
            "VALUES (%s, %s, SYSDATE)",
            (WATERMARK_KEY, new_watermark),
        )


# =============================================================================
# EXTRACT + LOAD
# =============================================================================
def fetch_new_bronze(db, watermark: str):
    """Return (mapped rows, max fetched_at seen) for adsb_raw docs newer than the watermark."""
    rows: list[dict] = []
    max_fetched = watermark
    cursor = db["adsb_raw"].find({"fetched_at": {"$gt": watermark}}).sort("fetched_at", 1)
    for doc in cursor:
        rows.extend(map_adsb_doc(doc))
        fetched_at = doc.get("fetched_at")
        if fetched_at and fetched_at > max_fetched:
            max_fetched = fetched_at
    return rows, max_fetched


def load_staging(cur, rows: list[dict]) -> None:
    """Create the session TEMP staging table and bulk-insert the batch."""
    cur.execute("DROP TABLE IF EXISTS stg_position;")
    cur.execute("CREATE TEMP TABLE stg_position (LIKE silver.aircraft_position);")

    loaded_at = datetime.now(timezone.utc)
    tuples = [
        tuple(r[c] if c != "loaded_at" else loaded_at for c in STAGING_COLS)
        for r in rows
    ]
    execute_values(
        cur,
        f"INSERT INTO stg_position ({', '.join(STAGING_COLS)}) VALUES %s",
        tuples,
        page_size=1000,
    )


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    log.info("=" * 60)
    log.info("SILVER HISTORY (incremental -> Redshift) START")
    log.info("=" * 60)

    db = get_mongo_db()
    conn = get_redshift_conn()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            watermark = read_watermark(cur)
            log.info(f"Watermark: {watermark}")

            rows, new_watermark = fetch_new_bronze(db, watermark)
            if not rows:
                log.info("No new Bronze positions since watermark — nothing to load.")
                conn.rollback()
                return

            log.info(f"Prepared {len(rows)} position rows from new Bronze docs.")
            load_staging(cur, rows)

            cur.execute(LOAD_SQL.read_text())          # insert-if-new + sessionize legs
            advance_watermark(cur, new_watermark)

        conn.commit()
        log.info(f"Committed. Watermark advanced to {new_watermark}.")
        log.info("SILVER HISTORY COMPLETE.")
    except Exception as e:
        conn.rollback()
        log.error(f"Load failed, rolled back — watermark NOT advanced: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
