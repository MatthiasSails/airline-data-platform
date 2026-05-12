# OpenSky Network API

Free real-time and historical flight data based on ADS-B signals.

- Website: https://opensky-network.org
- No official Swagger spec available
- Auth: OAuth2 Client Credentials Flow

## Authentication

Token endpoint:
```
POST https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token
Body: grant_type=client_credentials&client_id=...&client_secret=...
```

Use the returned `access_token` as `Authorization: Bearer <token>` header.

## Credit Limits

| Account type | Credits/day |
|---|---|
| Anonymous | 400 |
| Registered | 4,000 |
| Data feeder | 8,000 |

Credits remaining: `X-Rate-Limit-Remaining` response header.

## Endpoints Used

### Departures
```
GET /api/flights/departure?airport={ICAO}&begin={unix}&end={unix}
```
Returns flights that departed from airport in time window (max 7 days).

### Arrivals
```
GET /api/flights/arrival?airport={ICAO}&begin={unix}&end={unix}
```
Returns flights that arrived at airport in time window (max 7 days).

### Flight by Aircraft
```
GET /api/flights/aircraft?icao24={icao24}&begin={unix}&end={unix}
```
Returns all flights for a specific aircraft (max 30 days).

## Response Fields (Flights)

| Field | Type | Description |
|---|---|---|
| `icao24` | str | Aircraft ICAO24 transponder address |
| `callsign` | str | Flight callsign (e.g. "EWG1R") |
| `firstSeen` | int | Unix timestamp departure |
| `lastSeen` | int | Unix timestamp arrival |
| `estDepartureAirport` | str | ICAO code departure airport |
| `estArrivalAirport` | str | ICAO code arrival airport |
| `estDepartureAirportHorizDistance` | int | Horizontal distance to departure airport (m) |
| `estArrivalAirportHorizDistance` | int | Horizontal distance to arrival airport (m) |

## Notes

- Airport codes are **ICAO** format (4 letters), not IATA (3 letters)
  - EDDB = Berlin Brandenburg (BER in IATA)
  - EDDM = Munich (MUC in IATA)
- Time windows must not exceed 7 days per request
