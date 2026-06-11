"""
ETL: MongoDB Atlas Bronze  →  Supabase map1 (Silver)

Reads from two Bronze collections and merges into map1:
  - adsb_raw      (adsb.lol)          field format: ac[].hex/lat/lon/…
  - opensky_raw   (OpenSky /states/all) field format: states[] as index-list

Postgres target is controlled by SUPABASE_DB_HOST (default: localhost).

  - On aws-airline-1 (IPv6): set SUPABASE_DB_HOST=db.<ref>.supabase.co and
    connect directly — no tunnel needed.
  - Local dev (Mac has no global IPv6): leave SUPABASE_DB_HOST unset (→ localhost)
    and open an SSH tunnel through the VM first:
        ssh -i ~/.ssh/airline_vm -f -N \\
            -L 5432:db.<ref>.supabase.co:5432 \\
            ubuntu@63.185.229.117

Requires in .env (project root):
    MONGO_URI              read-only Atlas URI
    MONGO_DB               airline_landing
    SUPABASE_DB_HOST       Supabase Postgres host (optional; default localhost)
    SUPABASE_DB_PORT       Supabase Postgres port (optional; default 5432)
    SUPABASE_DB_PASSWORD   Supabase postgres user password
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def extract() -> tuple[list[dict], list[dict]]:
    client = MongoClient(os.environ["MONGO_URI"])
    db = client[os.environ.get("MONGO_DB", "airline_landing")]
    adsb_docs = list(db["adsb_raw"].find())
    states_docs = list(
        db["opensky_raw"].find({"endpoint": "/states/all"})
    )
    client.close()
    log.info("Extracted %d adsb_raw + %d opensky_raw (states) documents",
             len(adsb_docs), len(states_docs))
    return adsb_docs, states_docs


def _from_adsb(docs: list[dict], now: str) -> tuple[list[dict], int]:
    rows, skipped = [], 0
    for doc in docs:
        ts = doc.get("api_timestamp_ms")
        time_position = int(ts // 1000) if ts else None
        for ac in doc.get("ac") or []:
            lat, lon = ac.get("lat"), ac.get("lon")
            if lat is None or lon is None:
                skipped += 1
                continue
            rows.append({
                "icao24":        ac.get("hex"),
                "time_position": time_position,
                "callsign":      (ac.get("flight") or "").strip() or None,
                "longitude":     lon,
                "latitude":      lat,
                "on_ground":     ac.get("alt_baro") == "ground",
                "true_track":    ac.get("track"),
                "vertical_rate": ac.get("baro_rate"),
                "updated_at":    now,
            })
    return rows, skipped


def _from_opensky_states(docs: list[dict], now: str) -> tuple[list[dict], int]:
    # OpenSky state vector indices:
    # 0=icao24 1=callsign 2=origin_country 3=time_position 4=last_contact
    # 5=longitude 6=latitude 7=baro_altitude 8=on_ground 9=velocity
    # 10=true_track 11=vertical_rate
    rows, skipped = [], 0
    for doc in docs:
        for s in doc.get("states") or []:
            if s[5] is None or s[6] is None:
                skipped += 1
                continue
            rows.append({
                "icao24":        s[0],
                "time_position": s[3],
                "callsign":      (s[1] or "").strip() or None,
                "longitude":     s[5],
                "latitude":      s[6],
                "on_ground":     s[8] or False,
                "true_track":    s[10],
                "vertical_rate": s[11],
                "updated_at":    now,
            })
    return rows, skipped


def transform(adsb_docs: list[dict], states_docs: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    adsb_rows, adsb_skip = _from_adsb(adsb_docs, now)
    states_rows, states_skip = _from_opensky_states(states_docs, now)
    rows = adsb_rows + states_rows
    log.info(
        "Transformed %d rows (adsb=%d, opensky=%d; skipped=%d)",
        len(rows), len(adsb_rows), len(states_rows), adsb_skip + states_skip,
    )
    return rows


def load(rows: list[dict]) -> None:
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(
        host=os.environ.get("SUPABASE_DB_HOST", "localhost"),
        port=int(os.environ.get("SUPABASE_DB_PORT", "5432")),
        dbname="postgres",
        user="postgres",
        password=os.environ["SUPABASE_DB_PASSWORD"],
    )
    cols = ["icao24", "time_position", "callsign", "longitude", "latitude",
            "on_ground", "true_track", "vertical_rate", "updated_at"]
    sql = f"""
        INSERT INTO map1 ({", ".join(cols)})
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    with conn:
        with conn.cursor() as cur:
            batch = [tuple(r[c] for c in cols) for r in rows]
            psycopg2.extras.execute_values(cur, sql, batch, page_size=500)
    conn.close()
    log.info("Done — %d rows written to map1", len(rows))


if __name__ == "__main__":
    adsb_docs, states_docs = extract()
    if not adsb_docs and not states_docs:
        log.warning("No Bronze data found — run adsb_collector or opensky_states_collector first.")
    else:
        rows = transform(adsb_docs, states_docs)
        load(rows)
