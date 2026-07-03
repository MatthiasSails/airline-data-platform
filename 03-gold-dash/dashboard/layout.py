import dash_leaflet as dl
from dash import dcc, html

EDDF_LAT = 50.0379
EDDF_LON = 8.5622
DEFAULT_ZOOM = 11
POLL_INTERVAL_MS = 45_000


def build_layout() -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Frankfurt Airport Live Traffic", className="title"),
                    html.Div(id="status-line", className="status-line"),
                ],
                className="header",
            ),
            html.Div("this is dash", className="dash-marker"),
            dl.Map(
                center=[EDDF_LAT, EDDF_LON],
                zoom=DEFAULT_ZOOM,
                children=[
                    dl.TileLayer(),
                    dl.LayerGroup(id="aircraft-layer"),
                ],
                style={"width": "100%", "height": "80vh"},
                id="map",
            ),
            dcc.Interval(id="poll-interval", interval=POLL_INTERVAL_MS, n_intervals=0),
            dcc.Store(id="aircraft-store"),
        ],
        className="app-container",
    )
