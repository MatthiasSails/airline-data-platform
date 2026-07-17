import os
from datetime import datetime, timezone

import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Airline Live Map", layout="wide")
st.title("Live Flight Map")

# Env-injected target table so the same image serves prod (map1) and the Q stage
# environment (q_map1). Allowlist-restricted because it is interpolated as a SQL
# identifier (table names can't be bind params).
MAP_TABLE = os.environ.get("MAP_TABLE", "map1")
if MAP_TABLE not in {"map1", "q_map1"}:
    raise ValueError(f"MAP_TABLE must be 'map1' or 'q_map1', got {MAP_TABLE!r}")


def _conn():
    return psycopg2.connect(
        host=os.environ["SUPABASE_DB_HOST"],
        port=int(os.environ.get("SUPABASE_DB_PORT", "5432")),
        dbname="postgres",
        user="postgres",
        password=os.environ["SUPABASE_DB_PASSWORD"],
        connect_timeout=10,
    )


@st.cache_data(ttl=5)
def load_snapshot() -> pd.DataFrame:
    conn = _conn()
    # MAP_TABLE is allowlist-validated above, so this f-string interpolation is injection-safe.
    df = pd.read_sql(
        f"""
        SELECT DISTINCT ON (icao24, callsign)
               icao24, callsign, latitude, longitude, on_ground,
               true_track, vertical_rate, time_position
        FROM {MAP_TABLE}
        ORDER BY icao24, callsign, time_position DESC, id DESC
        """,
        conn,
    )
    conn.close()
    df["time_position"] = pd.to_datetime(df["time_position"], unit="s", utc=True)
    return df


df = load_snapshot()

if df.empty:
    st.warning(f"No data in {MAP_TABLE} — run the ETL first.")
    st.stop()

newest_position = df["time_position"].max()
c1, c2, c3 = st.columns(3)
c1.metric("Aircraft", len(df))
c2.metric("In flight", int((~df["on_ground"]).sum()))
c3.metric("Newest position", newest_position.strftime("%Y-%m-%d %H:%M UTC"))

st.subheader("Map")
st.map(df[["latitude", "longitude"]].dropna())

st.subheader("Aircraft")
st.dataframe(
    df[["icao24", "callsign", "latitude", "longitude", "on_ground",
        "true_track", "vertical_rate", "time_position"]]
    .sort_values("callsign")
    .rename(columns={
        "icao24":        "ICAO24",
        "callsign":      "Callsign",
        "latitude":      "Latitude",
        "longitude":     "Longitude",
        "on_ground":     "On Ground",
        "true_track":    "Track (°)",
        "vertical_rate": "Vertical Rate (m/s)",
        "time_position": "Time Position (UTC)",
    }),
    use_container_width=True,
)
