import os
import pandas as pd
import streamlit as st
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]

st.set_page_config(page_title="ADS-B Berlin", layout="wide")
st.title("ADS-B Landing Zone — Berlin")


@st.cache_resource
def get_collection():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client["airline_landing"]["adsb_raw"]


col = get_collection()

total_snapshots = col.count_documents({})
latest = col.find_one(sort=[("collected_at", -1)])

st.metric("Snapshots in DB", total_snapshots)

if not latest:
    st.warning("No snapshots found.")
    st.stop()

st.caption(f"Latest snapshot: {latest['collected_at']}  —  {latest['total']} aircraft")

aircraft = latest.get("ac", [])
df = pd.DataFrame(aircraft)

if not df.empty and {"lat", "lon"}.issubset(df.columns):
    st.subheader("Map")
    st.map(df[["lat", "lon"]].dropna())

st.subheader("Aircraft in latest snapshot")
show_cols = [c for c in ["flight", "hex", "lat", "lon", "alt_baro", "gs"] if c in df.columns]
st.dataframe(df[show_cols] if show_cols else df, use_container_width=True)
