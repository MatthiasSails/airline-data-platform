import os

import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Airline Live Map", layout="wide")
st.title("Live Flight Map")


def _conn():
    return psycopg2.connect(
        host=os.environ.get("SUPABASE_DB_HOST", "localhost"),
        port=5432,
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
        SELECT icao24, callsign, latitude, longitude,
               on_ground, true_track, updated_at
        FROM map1
        WHERE updated_at = (SELECT MAX(updated_at) FROM map1)
        """,
        conn,
    )
    conn.close()
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
    df[["icao24", "callsign", "latitude", "longitude", "on_ground", "true_track"]]
    .sort_values("callsign"),
    use_container_width=True,
)
