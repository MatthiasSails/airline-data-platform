# Lufthansa API Data Collection

Step 1 of the Airline Data Engineering project: **Data Discovery & Organization**

## Overview

Python tools to collect **Airports** and **Airlines** reference data from the Lufthansa Public API.

```
Lufthansa API (OAuth2)
        ↓
LufthansaAPIClient
        ↓
Collectors (Airports, Airlines)
        ↓
JSON Files (for MongoDB landing zone)
```

## Modes

### 🧪 Mock Mode (Development)
No credentials needed - uses pre-loaded sample data.

```python
from lufthansa_api.client import LufthansaAPIClient

client = LufthansaAPIClient(use_mock=True)
airports = client.get_airports()
airlines = client.get_airlines()
```

### 🔐 Real API Mode (Production)
Requires Lufthansa API credentials (OAuth2).

```python
client = LufthansaAPIClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    use_mock=False
)
```

Or use environment variables:
```bash
export LH_CLIENT_ID="your_client_id"
export LH_CLIENT_SECRET="your_client_secret"
```

## Quick Start

### 1. Demo with Mock Data
```bash
cd /Volumes/Rocket_2/DEV/git/Airline/03\ Data\ Collection
python demo.py
```

**Output:**
```
============================================================
DEMO: Lufthansa API Client (Mock Mode)
============================================================

1. Getting mock airports...
   Found 5 airports:
     - BER: Berlin Brandenburg
     - TXL: Berlin Tegel
     - CDG: Paris Charles de Gaulle
     ...

2. Getting mock airlines...
   Found 5 airlines:
     - LH: Lufthansa
     - BA: British Airways
     ...
```

### 2. Collect Real Data (when credentials arrive)
```bash
python collectors/airports_collector.py
python collectors/airlines_collector.py
```

### 3. Use in Your Code
```python
from lufthansa_api.client import LufthansaAPIClient
import json

client = LufthansaAPIClient(use_mock=True)

# Get all airports (paginated)
response = client.get_airports(limit=100, offset=0)
airports = response["ResourceResponse"]["Airport"]

# Get specific airport
ber = client.get_airports(airport_code="BER")

# Get nearest airports to coordinates
nearest = client.get_nearest_airports(latitude=52.5, longitude=13.4)

# Get all airlines
response = client.get_airlines(limit=100)
airlines = response["ResourceResponse"]["Airline"]

# Get specific airline
lh = client.get_airlines(airline_code="LH")
```

## API Endpoints (from Swagger 2.0)

### Airports

#### Get All Airports
```
GET /references/airports
Query Params:
  - limit: 1-100 (default: 20)
  - offset: skip N records (default: 0)
  - lang: 2-letter ISO language code (optional)
  - LHoperated: true/false - only LH-operated locations (optional)
```

#### Get Specific Airport
```
GET /references/airports/{airportCode}
  - airportCode: 3-letter IATA code (e.g., "BER", "CDG")
  - lang: language code (optional)
```

#### Get Nearest Airports
```
GET /references/airports/nearest/{latitude},{longitude}
  - latitude: -90 to +90
  - longitude: -180 to +180
  - lang: language code (optional)

Returns: 5 closest airports
```

### Airlines

#### Get All Airlines
```
GET /references/airlines
Query Params:
  - limit: 1-100 (default: 20)
  - offset: skip N records (default: 0)
```

#### Get Specific Airline
```
GET /references/airlines/{airlineCode}
  - airlineCode: 2-letter IATA code (e.g., "LH", "BA")
```

## Response Format

### Airports Response
```json
{
  "ResourceResponse": {
    "Airport": [
      {
        "AirportCode": "BER",
        "CityCode": "BER",
        "CountryCode": "DE",
        "LocationType": "Airport",
        "Names": {
          "Name": [
            {
              "@LanguageCode": "en",
              "$": "Berlin Brandenburg"
            }
          ]
        },
        "Position": {
          "Coordinate": {
            "Latitude": 52.364,
            "Longitude": 13.502
          }
        }
      }
    ]
  }
}
```

### Airlines Response
```json
{
  "ResourceResponse": {
    "Airline": [
      {
        "AirlineCode": "LH",
        "Names": {
          "Name": [
            {
              "@LanguageCode": "en",
              "$": "Lufthansa"
            }
          ]
        }
      }
    ]
  }
}
```

## File Structure

```
03-data-collection/
├── lufthansa_api/
│   ├── __init__.py           # Package exports
│   ├── client.py             # Main API client
│   ├── schemas.py            # Data models
│   └── mock_data.py          # Sample data for dev
├── collectors/
│   ├── airports_collector.py # Fetch & save airports
│   └── airlines_collector.py # Fetch & save airlines
├── data/
│   ├── airports.json         # Collected airport data
│   └── airlines.json         # Collected airline data
├── demo.py                   # Demo script
└── README.md                 # This file
```

## Next Steps

1. **Waiting for:** Lufthansa API Credentials (Client ID + Secret)
2. **Then:** Run collectors with real API:
   ```bash
   export LH_CLIENT_ID="..."
   export LH_CLIENT_SECRET="..."
   python collectors/airports_collector.py
   python collectors/airlines_collector.py
   ```
3. **Load data into MongoDB** for raw landing zone
4. **Analyze schemas** for PostgreSQL data warehouse design

## API Documentation

- Full Swagger spec: [`../02-api-docs/LH_public_API_swagger_2_0.json`](../02-api-docs/LH_public_API_swagger_2_0.json)
- Lufthansa API: https://developer.lufthansa.com/docs
- OAuth2 Flow: https://api.lufthansa.com/v1/oauth/token

## Authentication

The Lufthansa API uses OAuth2 (flow: `accessCode`).

- **Token Endpoint:** `https://api.lufthansa.com/v1/oauth/token`
- **Scopes:** `read:LH Open API`

See the Swagger spec for details.
