import os
from datetime import datetime, timezone

import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Airline Live Map", layout="wide")
st.title("Live Flight Map")


def _conn():
    return psycopg2.connect(
        host=os.environ["SUPABASE_DB_HOST"],
        port=int(os.environ.get("SUPABASE_DB_PORT", "5432")),
        dbname="postgres",
        user="postgres",
        password=os.environ["SUPABASE_DB_PASSWORD"],
        connect_timeout=10,
    )


@st.cache_data(ttl=300)
def load_snapshot() -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql(
        """
        SELECT icao24, callsign, latitude, longitude, on_ground,
               true_track, vertical_rate, time_position, updated_at
        FROM map1
        WHERE updated_at = (SELECT MAX(updated_at) FROM map1)
        """,
        conn,
    )
    conn.close()
    df["time_position"] = pd.to_datetime(df["time_position"], unit="s", utc=True)
    return df


df = load_snapshot()

if df.empty:
    st.warning("No data in map1 — run the ETL first.")
    st.stop()

snapshot_time = df["updated_at"].iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Aircraft", len(df))
c2.metric("In flight", int((~df["on_ground"]).sum()))
c3.metric("Snapshot", snapshot_time.strftime("%Y-%m-%d %H:%M UTC"))

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
