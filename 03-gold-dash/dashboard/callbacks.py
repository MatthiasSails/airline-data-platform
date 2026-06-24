import os
from datetime import datetime, timezone

import dash_leaflet as dl
import httpx
from dash import Dash, Input, Output, html

from icons import aircraft_icon_html, vertical_trend_label

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 10.0


def register_callbacks(app: Dash) -> None:
    @app.callback(Output("aircraft-store", "data"), Input("poll-interval", "n_intervals"))
    def fetch_aircraft(_n_intervals: int) -> list[dict]:
        try:
            response = httpx.get(f"{API_BASE_URL}/aircraft/current", timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return []

    @app.callback(Output("aircraft-layer", "children"), Input("aircraft-store", "data"))
    def render_markers(aircraft: list[dict] | None) -> list[dl.DivMarker]:
        if not aircraft:
            return []

        markers = []
        for ac in aircraft:
            lat = ac.get("latitude")
            lon = ac.get("longitude")
            if lat is None or lon is None:
                continue

            label = ac.get("callsign") or ac.get("icao24") or "Unknown"
            ground_text = "On ground" if ac.get("on_ground") else "Airborne"
            trend_text = vertical_trend_label(ac.get("vertical_rate"))
            tooltip_text = f"{label} — {ground_text} — {trend_text}"

            markers.append(
                dl.DivMarker(
                    position=[lat, lon],
                    iconOptions={
                        "html": aircraft_icon_html(
                            ac.get("true_track"),
                            ac.get("on_ground"),
                            ac.get("vertical_rate"),
                        ),
                        "className": "",
                    },
                    children=[dl.Tooltip(tooltip_text)],
                )
            )
        return markers

    @app.callback(Output("status-line", "children"), Input("aircraft-store", "data"))
    def render_status_line(aircraft: list[dict] | None) -> str:
        if not aircraft:
            return "0 aircraft — last updated: n/a"

        count = len(aircraft)
        timestamps = [ac.get("updated_at") for ac in aircraft if ac.get("updated_at")]
        if not timestamps:
            return f"{count} aircraft — last updated: n/a"

        freshest = max(datetime.fromisoformat(ts) for ts in timestamps)
        freshest_local = freshest.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"{count} aircraft — last updated: {freshest_local}"
