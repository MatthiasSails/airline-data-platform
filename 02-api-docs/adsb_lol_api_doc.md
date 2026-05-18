# adsb.lol API Documentation

Real-time global aircraft tracking via community ADS-B receiver network.

- **Website:** https://adsb.lol
- **API Docs:** https://api.adsb.lol/docs
- **GitHub:** https://github.com/adsblol/api
- **License:** ODbL (Open Data Commons Open Database License)
- **Auth:** None required (currently public; future: API key for feeders)

---

## Overview

adsb.lol is a community-driven, open-source flight tracking service that aggregates ADS-B signals from thousands of independent receivers worldwide. It is a drop-in replacement API for the commercial ADSBExchange.com service but with no cost or licensing restrictions.

**Key Characteristics:**
- Live aircraft positions updated continuously (500ms granularity from receiver network)
- Global coverage via decentralized receiver community
- Uses ICAO24 hex codes (8-digit aircraft identifiers)
- Zero cost, no API key required (as of 2026-05-13)
- Open-source architecture (Python/asyncio/aiohttp, Kubernetes)

---

## Authentication

**Currently:** No authentication required. API is public.

**Future Plan:** API keys will be introduced (not yet active). When implemented, keys will be obtained by contributing to the network (becoming a data feeder).

All endpoints are accessed directly via HTTP GET without authentication headers.

---

## Rate Limiting

**Policy:** Dynamic rate limiting based on server load.

**Guidance from maintainers:**
- No published hard limit
- If you receive 4xx status codes, you are likely violating best practices (e.g., hammering endpoints in a loop)
- Proper implementation (with backoff and reasonable intervals) will not be rate-limited
- Recommended: 30–60 second intervals for periodic requests

**For Data Engineering context:**
- Batch requests are fine (collect aircraft by region/time window)
- Don't poll individual aircraft position endpoints faster than once per 10 seconds
- Batch aggregation queries are encouraged

---

## Base URL

```
https://api.adsb.lol/v2
```

All endpoints are relative to this base.

> **Note:** The interactive docs at api.adsb.lol/docs show `/api/v2/` — this returns 404. Verified working base is `/v2/` (tested 2026-05-18).

---

## Endpoints

### Get All Aircraft by Geographic Area

**Request:**
```
GET /lat/{lat}/lon/{lon}/dist/{dist}
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `lat` | float | Latitude (-90 to +90) |
| `lon` | float | Longitude (-180 to +180) |
| `dist` | int | Radius in nautical miles (e.g., 25, 100) |

**Response:**
```json
{
  "ctime": 1715632800,
  "aircraft": [
    {
      "hex": "780338",
      "type": "adsb_icao",
      "flight": "DLH123",
      "r": "N503NK",
      "t": "B737",
      "alt_baro": 35000,
      "alt_geom": 35420,
      "gs": 450,
      "track": 270.5,
      "baro_rate": 500,
      "squawk": "0001",
      "emergency": null,
      "category": "A3",
      "nav_qnh": 1013.25,
      "nav_altitude_mcp": 35000,
      "nav_heading": 270,
      "lat": 52.5,
      "lon": 13.4,
      "nic": 8,
      "rc": 186,
      "seen_pos": 1.5,
      "seen": 0.2,
      "rssi": -21.5
    }
  ]
}
```

**Response Fields (Aircraft Object):**
| Field | Type | Description |
|-------|------|-------------|
| `hex` | str | ICAO24 hex code (8 digits) |
| `flight` | str | Callsign (e.g., "LH123") |
| `r` | str | Registration (tail number, e.g., "N503NK") |
| `t` | str | Aircraft type (ICAO code, e.g., "B737") |
| `alt_baro` | int | Barometric altitude (feet) |
| `alt_geom` | int | Geometric altitude (feet) |
| `gs` | float | Ground speed (knots) |
| `track` | float | Track (heading, 0–360 degrees) |
| `baro_rate` | int | Vertical speed (feet/minute) |
| `squawk` | str | Transponder squawk code (4 digits) |
| `category` | str | Aircraft category (A0–C3, for size) |
| `lat` | float | Latitude |
| `lon` | float | Longitude |
| `seen_pos` | float | Seconds since last position update |
| `seen` | float | Seconds since last message from this aircraft |
| `rssi` | float | Signal strength (RSSI in dBFS) |

---

### Get Aircraft by ICAO24 Hex

**Request:**
```
GET /hex/{icao24}
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `icao24` | str | ICAO24 hex code (8 hex digits, case-insensitive) |

**Response:**
```json
{
  "ctime": 1715632800,
  "aircraft": [
    { /* same aircraft object as above */ }
  ]
}
```

---

### Get Aircraft by Callsign

**Request:**
```
GET /callsign/{callsign}
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `callsign` | str | Flight callsign (e.g., "DLH123" or "LH*" for wildcard) |

**Response:**
Same format as geographic query (array of aircraft objects).

---

### Get Aircraft by Registration (Tail Number)

**Request:**
```
GET /reg/{registration}
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `registration` | str | Tail number (e.g., "N503NK") |

**Response:**
Same format (array of aircraft objects).

---

### Get Aircraft by Squawk Code

**Request:**
```
GET /squawk/{squawk}
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `squawk` | str | 4-digit squawk code (e.g., "0001") |

**Response:**
Same format (array of aircraft objects).

---

## Data Format & Schema

### Key Differences from OpenSky

| Feature | OpenSky | adsb.lol |
|---------|---------|----------|
| **Airport Codes** | ICAO (4 chars: EDDB) | None (raw positions only) |
| **Flight Callsigns** | Optional, sometimes missing | Usually present |
| **Registration (Tail)** | Not provided | Provided (`r` field) |
| **Aircraft Type** | Not provided | Provided (`t` field: ICAO code) |
| **Altitude** | Single value | Baro + geometric dual altitude |
| **Timestamps** | Explicit (firstSeen, lastSeen) | Response ctime only; age via `seen_pos` |
| **Update Frequency** | Periodic (request-based) | Continuous (500ms from network) |
| **Rate Limiting** | Hard limits (4k–8k req/day) | Dynamic/generous |

### What adsb.lol Does NOT Provide

- Airport departure/arrival pairs (use OpenSky or Lufthansa API for scheduled flights)
- Historical data (only live positions)
- Structured flight schedule (use other APIs for that)
- IATA codes (use a separate ICAO→IATA mapping table)

---

## Common Use Cases & Examples

### Use Case 1: Track Aircraft Near Berlin

```bash
curl "https://api.adsb.lol/v2/lat/52.52/lon/13.41/dist/25"
```

Returns all aircraft within 25 nautical miles of Berlin city center.

**For Python:**
```python
import requests

response = requests.get(
    "https://api.adsb.lol/v2/lat/52.52/lon/13.41/dist/25"
)
aircraft = response.json()["ac"]  # key is "ac", not "aircraft"
for a in aircraft:
    print(f"{a['hex']}: {a.get('flight', 'N/A')} at {a['alt_baro']}ft")
```

---

### Use Case 2: Track Specific Aircraft by Hex Code

```python
icao24 = "780338"  # Example hex code
response = requests.get(f"https://api.adsb.lol/v2/hex/{icao24}")
```

---

### Use Case 3: Find Aircraft by Callsign (Wildcard)

```python
response = requests.get("https://api.adsb.lol/v2/callsign/DLH")
# Returns all Lufthansa flights currently tracked (ICAO callsign prefix "DLH", not IATA "LH")
```

---

## Integration with Project (Phase 2)

### Data Pipeline

```
adsb.lol API (geographic/callsign query)
        ↓
Python collector (batch queries by region)
        ↓
Raw JSON → MongoDB (landing zone)
        ↓
ETL: flatten, normalize, validate
        ↓
PostgreSQL (positions table with timestamps)
```

### Expected Schema (MongoDB)

```json
{
  "_id": ObjectId(),
  "collected_at": ISODate("2026-05-13T12:34:56Z"),
  "query_type": "lat_lon_dist",
  "query_params": {"lat": 52.52, "lon": 13.41, "dist": 25},
  "ctime": 1715632800,
  "aircraft": [
    { /* full aircraft object from API */ }
  ]
}
```

### PostgreSQL Derived Table (Flatten Example)

```sql
CREATE TABLE adsb_positions (
    hex                VARCHAR(8)    NOT NULL,
    callsign           VARCHAR(10),
    registration       VARCHAR(10),
    aircraft_type      VARCHAR(4),
    latitude           FLOAT         NOT NULL,
    longitude          FLOAT         NOT NULL,
    altitude_baro      INT,
    altitude_geom      INT,
    ground_speed       FLOAT,
    track              FLOAT,
    vertical_rate      INT,
    squawk             VARCHAR(4),
    seen_at            TIMESTAMP     NOT NULL,
    collected_at       TIMESTAMP     NOT NULL,
    
    PRIMARY KEY (hex, collected_at)
);
```

---

## Notes & Constraints

1. **No Historical Lookback:** Unlike OpenSky (1 hour), adsb.lol only provides live positions. Archive to database for historical analysis.

2. **No Airport Codes:** adsb.lol does not resolve lat/lon to airport codes. Use a separate GIS database or join with airports table via distance queries.

3. **ICAO24 Mapping:** Aircraft hex codes (`780338`) do not directly map to airports or airlines. Use external reference data.

4. **Community Network:** Coverage varies by region. Dense receiver networks in Europe/US; sparse elsewhere.

5. **Duplicate Data Risk:** Same aircraft may appear in multiple API responses if queried with overlapping geographic regions. Deduplication needed in ETL.

6. **Real-Time vs. Batch:** Suitable for both:
   - Batch collection (periodic queries by region → MongoDB)
   - Real-time dashboards (query by callsign/hex on-demand)

7. **`alt_baro` mixed type — ETL gotcha:** The `alt_baro` field is **not a clean integer**. Aircraft on the ground return the string `"ground"` instead of a number. ETL must handle this explicitly:
   ```python
   df["alt_baro_ft"] = pd.to_numeric(df["alt_baro"], errors="coerce")  # "ground" → NaN
   df["on_ground"] = df["alt_baro"] == "ground"
   ```
   Never cast `alt_baro` directly to `int` — it will raise on ground-based aircraft.

8. **Response key is `ac`, not `aircraft`:** The aircraft array in the JSON response is under the key `"ac"`, not `"aircraft"` as some older docs suggest. The top-level response also contains `total`, `now`, `ctime`, `ptime`, and `msg`.

---

## Comparison: adsb.lol vs ADSBExchange (RapidAPI)

Both offer similar API contracts. adsb.lol is preferred because:

| Dimension | adsb.lol | ADSBExchange RapidAPI |
|-----------|----------|----------------------|
| **Cost** | Free | $10/month |
| **Auth** | None | API key |
| **Rate Limit** | Dynamic (generous) | 10k req/month |
| **Licensing** | ODbL (open) | Non-commercial only |
| **API Compatibility** | Drop-in replacement | Standard |

---

## References

- adsb.lol GitHub: https://github.com/adsblol/api
- adsb.lol Interactive Docs: https://api.adsb.lol/docs
- ICAO24 Aircraft Database: https://www.icao.int/
- OpenSky Network (complementary): https://opensky-network.org

---

## Related Documentation

- `airline_api_market_overview.md` — Market comparison
- `adr_003_adsb_lol_dual_stream_strategy.md` — Why we chose adsb.lol for Phase 2
- `opensky_api_doc.md` — Complementary structured API
