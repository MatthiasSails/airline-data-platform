# Frankfurt Airport Live Traffic Dashboard — Development Spec

## Scope

Build the **API** and **dashboard** layers only, plus **deployment** to AWS Lightsail. The data ingestion layer (OpenSky poller → Postgres) is already built and out of scope — the table `map1` already exists, is already scoped to the Frankfurt area, and is already kept as one upserted row per aircraft (no deduplication needed).

This spec covers three components:
1. A read-only **FastAPI** service that queries Postgres (hosted on Supabase).
2. A **Dash** dashboard that polls the API every 45 seconds and renders aircraft on a map.
3. **Deployment** of both on a single AWS Lightsail VM (2 GB RAM, 2 vCPU, 60 GB SSD, x86_64) behind Nginx.

---

## 1. Data source: `map1` table (Supabase Postgres)

Already populated by an external poller. Do not write to this table from the API.

```
id              int8        PK identity
created_at      timestamptz
icao24          varchar     nullable
time_position   int4        nullable
callsign        varchar     nullable
longitude       float4      nullable
latitude        float4      nullable
on_ground       bool        nullable
true_track      float8      nullable
vertical_rate   float8      nullable
updated_at      timestamptz nullable
```

Important facts about this data, confirmed with the project owner:
- `icao24` is unique in practice — one row per aircraft, upserted by the poller. No GROUP BY / dedup logic needed.
- The table is already pre-filtered to the Frankfurt area. No bounding-box filtering needed in the API.
- Every column except `id`/`created_at` is nullable. The API and dashboard must handle `NULL` defensively (see field-specific rules below) rather than assuming values are always present.
- There is **no altitude or velocity column** in this table. Do not reference these fields anywhere (API responses, tooltips, table views).
- `vertical_rate` is in **meters/second**, **positive = climbing, negative = descending** (OpenSky convention).
- `true_track` is in degrees, **clockwise from north** (0° = north), which matches CSS `rotate()` convention directly — no conversion needed.

---

## 2. FastAPI service

### 2.1 Endpoints

**`GET /aircraft/current`**
Returns all currently valid aircraft rows.

```sql
SELECT icao24, callsign, longitude, latitude, on_ground, true_track, vertical_rate, updated_at
FROM map1
WHERE longitude IS NOT NULL AND latitude IS NOT NULL
```

The `NULL` lat/lon filter is the only defensive filter required — rows without coordinates can't be plotted and should be dropped at the query level rather than handled downstream. Do not add bounding-box or `icao24` dedup logic; both are already handled upstream.

**`GET /health`**
Runs `SELECT 1` against the database; returns 200/OK or a clear error. Used for monitoring and deployment verification.

### 2.2 Response model (Pydantic)

```python
from datetime import datetime
from pydantic import BaseModel

class Aircraft(BaseModel):
    icao24: str | None
    callsign: str | None
    longitude: float | None
    latitude: float | None
    on_ground: bool | None
    true_track: float | None
    vertical_rate: float | None
    updated_at: datetime | None
```

All fields optional, mirroring the nullable columns honestly. The lat/lon `NOT NULL` guarantee is enforced in SQL, not by changing these types to non-optional.

### 2.3 Database access

- Use `asyncpg` or SQLAlchemy 2.0 async engine, connecting to Supabase via its Postgres connection string (session or direct connection, not the transaction pooler meant for serverless/edge use cases).
- Small connection pool (2–5 connections) — the only consumer is the Dash app polling every 45 seconds.
- Read-only. No `INSERT`/`UPDATE`/`DELETE` statements anywhere in this service.
- Load the Supabase connection string from environment variables (`.env`, not committed to version control).

### 2.4 CORS

Not required if Dash calls FastAPI server-side over `localhost` (see §3.1 and §4.1 — this is the default approach in this spec). Only add CORS configuration if a decision is later made to expose the API to browser-side or third-party consumers.

### 2.5 Suggested structure

```
api/
├── main.py              # FastAPI app, route registration
├── models.py            # Pydantic models (Aircraft, etc.)
├── db.py                # async engine/session/connection pool setup
├── routers/
│   └── aircraft.py       # /aircraft/current endpoint
└── requirements.txt
```

---

## 3. Dash dashboard

### 3.1 Data flow

- `dcc.Interval` component, `interval=45000` (milliseconds).
- On each tick, a callback calls FastAPI's `/aircraft/current` over `http://127.0.0.1:8000/aircraft/current` (server-side HTTP call using `httpx` or `requests` — **not** a browser-side fetch). This keeps FastAPI bound to localhost only, with no public exposure and no CORS needed.
- Response is stored in a `dcc.Store`, which drives re-rendering of the map's marker layer.

### 3.2 Map: dash-leaflet with custom rotated icons

- `dl.Map` + `dl.TileLayer`, centered on Frankfurt Airport (EDDF): latitude `50.0379`, longitude `8.5622`. Default zoom level ~10–11.
- **Use `dl.DivMarker`, not `dl.Marker`**, for each aircraft. `dl.Marker` has no built-in rotation parameter; `DivMarker` allows injecting raw HTML/SVG with a CSS `transform: rotate()`, which is the correct mechanism here.
- All aircraft markers grouped in a single `dl.LayerGroup`, fully rebuilt from the `dcc.Store` contents on every 45-second tick. At Frankfurt-area traffic volumes, a full rebuild each cycle is simpler and sufficiently performant — no need for incremental/partial marker updates.

### 3.3 Aircraft icon design

Each marker is a composite of two independent visual elements:

| Field | Drives | Rule |
|---|---|---|
| `true_track` | Plane silhouette rotation | Rotate by `true_track` degrees (clockwise, CSS-native). If `NULL`, default to `0°` (pointing north). |
| `on_ground` | Plane silhouette color | `true` → grey (`#9ca3af`). `false` **or `NULL`** → blue (`#2563eb`). **`NULL` defaults to airborne/blue.** |
| `vertical_rate` | Small arrow badge (separate from the plane icon, not rotated with it) | `> +1.0 m/s` → climbing (▲, green). `< -1.0 m/s` → descending (▼, red). Between `-1.0` and `+1.0`, or `NULL` → no arrow shown (level flight or unknown). |

The ±1.0 m/s deadband on `vertical_rate` avoids flickering an arrow on/off due to GPS-level noise during genuinely level flight.

The vertical-rate arrow represents a different physical axis (climb/descend) than the plane's heading, so it must **not** rotate along with the plane silhouette — it stays upright regardless of `true_track`.

#### Icon generator (`dashboard/icons.py`)

```python
def aircraft_icon_html(
    true_track: float | None,
    on_ground: bool | None,
    vertical_rate: float | None,
) -> str:
    angle = true_track if true_track is not None else 0
    is_on_ground = bool(on_ground) if on_ground is not None else False  # NULL -> airborne
    color = "#9ca3af" if is_on_ground else "#2563eb"

    VR_THRESHOLD = 1.0  # m/s deadband
    if vertical_rate is None or abs(vertical_rate) < VR_THRESHOLD:
        arrow_svg = ""
    elif vertical_rate > 0:
        arrow_svg = '<div class="vr-arrow vr-climb">&#9650;</div>'  # ▲
    else:
        arrow_svg = '<div class="vr-arrow vr-descend">&#9660;</div>'  # ▼

    return f'''
    <div style="position: relative; width: 32px; height: 32px;">
      <div style="transform: rotate({angle}deg); transform-origin: center;
                  width: 24px; height: 24px;">
        <svg width="24" height="24" viewBox="0 0 24 24">
          <path d="M12 2 L15 11 L22 15 L15 16 L16 22 L12 19 L8 22 L9 16 L2 15 L9 11 Z"
                fill="{color}" />
        </svg>
      </div>
      {arrow_svg}
    </div>
    '''
```

Companion CSS (in the Dash app's stylesheet, not inline per-marker since it's static styling):

```css
.vr-arrow { position: absolute; top: -2px; right: -2px; font-size: 12px; line-height: 1; }
.vr-climb { color: #16a34a; }
.vr-descend { color: #dc2626; }
```

Use this `aircraft_icon_html(...)` output as the `html` value inside each `dl.DivMarker`'s `iconOptions`.

### 3.4 Tooltips

Each `dl.DivMarker` should include a `dl.Tooltip` (or `dl.Popup`) showing, in plain text:
- `callsign` if present, otherwise fall back to `icao24`.
- Ground status: "On ground" or "Airborne".
- Vertical trend: "Climbing", "Descending", or "Level" (mirroring the same threshold logic as the arrow badge, for accessibility/clarity beyond the glyph alone).

### 3.5 Status line

A small header above the map showing:
- Total aircraft count in the current batch.
- "Last updated" timestamp, derived from the **freshest `updated_at` value in the returned batch** (not the wall-clock time of the Dash fetch). This way, if the upstream poller stalls, the dashboard visibly reflects stale data even though Dash's own polling is still running fine.

### 3.6 Optional (not required for v1, cheap to add later)

A `dash.DataTable` below the map listing visible aircraft (callsign, ground status, vertical trend) for a sortable list view alongside the map.

### 3.7 Suggested structure

```
dashboard/
├── app.py               # Dash app instantiation, layout assembly
├── layout.py             # Map, header, interval, store component definitions
├── callbacks.py           # Interval -> API fetch -> Store -> marker layer render
├── icons.py               # aircraft_icon_html() and related constants
├── assets/
│   └── style.css          # .vr-arrow, .vr-climb, .vr-descend rules
└── requirements.txt
```

---

## 4. Deployment: AWS Lightsail (2 GB RAM, 2 vCPU, 60 GB SSD, x86_64)

### 4.1 Process architecture

Two services, both managed by **systemd**, both bound to localhost — only Nginx is publicly exposed.

- **FastAPI**: `uvicorn api.main:app --host 127.0.0.1 --port 8000`
- **Dash**: `gunicorn dashboard.app:server --bind 127.0.0.1:8050 --workers 2`
  (`server` is Dash's underlying Flask object, exposed via `app.server` in `app.py`.)

### 4.2 Nginx reverse proxy

Single public-facing entry point on ports 80/443:
- `/` → proxied to `127.0.0.1:8050` (Dash)
- FastAPI is **not** exposed publicly in this design — Dash talks to it over localhost only (§3.1). If the API needs to be public later (e.g. for other consumers), add a `/api/` location block proxying to `127.0.0.1:8000` and add CORS to FastAPI at that point.

### 4.3 Secrets

`.env` file (excluded from version control) containing the Supabase Postgres connection string. Loaded via `python-dotenv` or systemd's `EnvironmentFile=` directive. Only the FastAPI service needs this — Dash never connects to Postgres directly.

### 4.4 Firewall

Via the Lightsail networking tab, open only:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS, if a domain + Certbot/Let's Encrypt TLS is set up)

### 4.5 Resource notes

At this scale (single dashboard, 45-second polling interval, Frankfurt-area aircraft counts), 2 GB RAM comfortably fits two small Python processes plus Nginx. Adding a 1 GB swap file is cheap insurance but not strictly required at this load.

### 4.6 Suggested deployment files

```
deploy/
├── fastapi.service
├── dash.service
└── nginx.conf
```

---

## 5. Full repository structure

```
opensky-frankfurt/
├── api/
│   ├── main.py
│   ├── models.py
│   ├── db.py
│   ├── routers/
│   │   └── aircraft.py
│   └── requirements.txt
├── dashboard/
│   ├── app.py
│   ├── layout.py
│   ├── callbacks.py
│   ├── icons.py
│   ├── assets/
│   │   └── style.css
│   └── requirements.txt
├── deploy/
│   ├── fastapi.service
│   ├── dash.service
│   └── nginx.conf
├── .env.example
└── README.md
```

---

## 6. Build order

1. **FastAPI**: implement `/aircraft/current` and `/health` against the real `map1` table. Verify via the auto-generated Swagger UI (`/docs`) that real rows come back correctly typed, including nullable fields and the lat/lon filter.
2. **Dash skeleton**: static `dl.Map` + `dl.TileLayer` centered on EDDF, no live data yet. Confirm the base map renders.
3. **Wire the data flow**: `dcc.Interval` → server-side FastAPI call → `dcc.Store`. Confirm with a debug print or temporary table view that real rows arrive correctly typed, especially around `NULL` handling.
4. **Add the `DivMarker` layer** incrementally:
   a. Static, unrotated, single-color markers first.
   b. Add `true_track`-based rotation.
   c. Add `on_ground`-based coloring (remembering the `NULL` → airborne/blue default).
   d. Add the `vertical_rate` arrow badge.
5. **Add the status line** (aircraft count + freshest `updated_at`) and tooltips.
6. **Write systemd unit files and the Nginx config**; test locally or on a throwaway instance if possible.
7. **Deploy to the real Lightsail VM**; verify end-to-end against live data flowing from the existing poller.

---

## 7. Explicitly out of scope

- The OpenSky poller and its OAuth2/credential handling (already built).
- Any write path to `map1` from the API or dashboard.
- Historical flight tracking / trajectory storage (live snapshot only, per existing design).
- Altitude or velocity display (no such columns exist in `map1`).
