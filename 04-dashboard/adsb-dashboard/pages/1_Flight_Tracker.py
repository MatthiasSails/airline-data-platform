import os
import pandas as pd
import streamlit as st
import pydeck as pdk
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]

st.set_page_config(page_title="Flight Tracker", layout="wide")
st.title("Flight Tracker")


@st.cache_resource
def get_collection():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client["airline_landing"]["flight_tracker_raw"]


col = get_collection()

flight_label = st.text_input("Flight label", value="EW7755")


@st.fragment(run_every="30s")
def live_map(label: str):
    docs = list(col.find({"flight_label": label}, sort=[("collected_at", 1)]))

    if not docs:
        st.warning(f"No data for {label} yet — is the collector running?")
        return

    df = pd.DataFrame(docs)
    current = df.iloc[-1]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Flight", label)
    c2.metric("Registration", current.get("registration") or "—")
    c3.metric("Altitude", f"{current.get('alt_baro', '?')} ft")
    c4.metric("Speed", f"{int(current.get('gs') or 0)} kts")
    c5.metric("Track", f"{int(current.get('track') or 0)}°")

    st.caption(
        f"Last update: {current['collected_at']}  |  {len(df)} positions collected  |  "
        f"Refreshes every 30 s"
    )

    path_coords = [[row["lon"], row["lat"]] for _, row in df.iterrows()]

    lat_center = (df["lat"].min() + df["lat"].max()) / 2
    lon_center = (df["lon"].min() + df["lon"].max()) / 2

    trail_layer = pdk.Layer(
        "PathLayer",
        [{"path": path_coords}],
        get_path="path",
        get_color=[255, 165, 0],
        width_min_pixels=3,
    )

    position_layer = pdk.Layer(
        "ScatterplotLayer",
        [{"lon": current["lon"], "lat": current["lat"]}],
        get_position=["lon", "lat"],
        get_fill_color=[220, 30, 30],
        get_radius=12000,
    )

    view = pdk.ViewState(
        latitude=lat_center,
        longitude=lon_center,
        zoom=5,
        pitch=0,
    )

    st.pydeck_chart(pdk.Deck(layers=[trail_layer, position_layer], initial_view_state=view))


live_map(flight_label)
