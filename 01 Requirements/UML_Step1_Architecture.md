# UML Diagram - Step 1 Data Architecture

## Entity Relationship Diagram (Airports + Airlines)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATABASE LAYER SCHEMA                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌──────────────────┐
│   AIRLINE        │
├──────────────────┤
│ code: VARCHAR(2) │ PRIMARY KEY
│ name: VARCHAR    │
│ alliance: VARCHAR│ (optional)
│ loaded_at: TS    │
└──────────────────┘


┌──────────────────────────────┐
│   AIRPORT                    │
├──────────────────────────────┤
│ code: VARCHAR(3)             │ PRIMARY KEY
│ name: VARCHAR                │
│ city_code: VARCHAR(3)        │
│ country_code: VARCHAR(2)     │
│ latitude: DECIMAL(10,6)      │
│ longitude: DECIMAL(10,6)     │
│ timezone: VARCHAR            │
│ location_type: VARCHAR       │
│ is_lh_operated: BOOLEAN      │
│ loaded_at: TIMESTAMP         │
└──────────────────────────────┘
```

---

## Data Flow: Ingestion → Processing → Serving

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: INGESTION                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Lufthansa API                                                              │
│  ├─ GET /references/airports/{code}                                         │
│  │   Response: {"ResourceResponse": {"Airport": [{...}, ...]}}              │
│  │                                                                           │
│  └─ GET /references/airlines/{code}                                         │
│      Response: {"ResourceResponse": {"Airline": [{...}, ...]}}              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STORAGE: MongoDB (Raw Landing Zone)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  db.airports:                                                               │
│  {                                                                          │
│    "_id": "TXL",                                                            │
│    "api_response": { /* full API response */ },                            │
│    "fetched_at": ISODate("2024-05-10T..."),                               │
│    "city_code": "BER",                                                      │
│    "country_code": "DE"                                                     │
│  }                                                                          │
│                                                                              │
│  db.airlines:                                                               │
│  {                                                                          │
│    "_id": "LH",                                                             │
│    "api_response": { /* full API response */ },                            │
│    "fetched_at": ISODate("2024-05-10T...")                                │
│  }                                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: PROCESSING (Python ETL)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. EXTRACT: Read from MongoDB                                              │
│     mongodb_airports → Python List[Dict]                                    │
│                                                                              │
│  2. TRANSFORM: Normalize API response                                       │
│     API Response nested JSON:                                               │
│     {                                                                       │
│       "AirportCode": "TXL",                                                 │
│       "Names": {                                                            │
│         "Name": [                                                           │
│           {"@LanguageCode": "en", "$": "Berlin Tegel"}                     │
│         ]                                                                   │
│       },                                                                    │
│       "Position": {"Coordinate": {"Latitude": 52.562, "Longitude": 13.288}}│
│     }                                                                       │
│                                                                              │
│     → Normalized Row:                                                       │
│     {                                                                       │
│       "code": "TXL",                                                        │
│       "name": "Berlin Tegel",                                               │
│       "latitude": 52.562,                                                   │
│       "longitude": 13.288,                                                  │
│       "city_code": "BER",                                                   │
│       "country_code": "DE"                                                  │
│     }                                                                       │
│                                                                              │
│  3. VALIDATE: Data quality checks                                           │
│     - code NOT NULL                                                         │
│     - latitude/longitude valid ranges                                       │
│                                                                              │
│  4. OUTPUT: CSV format                                                      │
│     airports.csv:                                                           │
│     code,name,city_code,country_code,latitude,longitude,...                │
│     TXL,Berlin Tegel,BER,DE,52.562,13.288,...                              │
│     CDG,Paris Charles de Gaulle,PAR,FR,49.009,2.548,...                    │
│                                                                              │
│     airlines.csv:                                                           │
│     code,name,alliance                                                      │
│     LH,Lufthansa,Star Alliance                                              │
│     BA,British Airways,OneWorld                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: SERVING (PostgreSQL + Neo4j)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PostgreSQL (Relational):                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Table: airports                                                    │    │
│  ├─────────────────┬──────────────┬─────────────────────────────────┤    │
│  │ code (PK)       │ name         │ city_code, country_code         │    │
│  │ VARCHAR(3)      │ VARCHAR(255) │ latitude, longitude, timezone   │    │
│  ├─────────────────┼──────────────┼─────────────────────────────────┤    │
│  │ TXL             │ Berlin Tegel │ BER, DE, 52.562, 13.288         │    │
│  │ CDG             │ Paris CDG    │ PAR, FR, 49.009, 2.548          │    │
│  │ ...             │ ...          │ ...                             │    │
│  └─────────────────┴──────────────┴─────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Table: airlines                                                    │    │
│  ├─────────────────┬──────────────┬─────────────────────────────────┤    │
│  │ code (PK)       │ name         │ alliance                        │    │
│  │ VARCHAR(2)      │ VARCHAR(255) │ VARCHAR                         │    │
│  ├─────────────────┼──────────────┼─────────────────────────────────┤    │
│  │ LH              │ Lufthansa    │ Star Alliance                   │    │
│  │ BA              │ British Airw │ OneWorld                        │    │
│  │ ...             │ ...          │ ...                             │    │
│  └─────────────────┴──────────────┴─────────────────────────────────┘    │
│                                                                              │
│  Neo4j (Graph):                                                             │
│  ┌─ Nodes:                                                                  │
│  │  (:Airport {code: "TXL", name: "Berlin Tegel", ...})                    │
│  │  (:Airline {code: "LH", name: "Lufthansa", ...})                        │
│  │                                                                          │
│  └─ Relationships (Future - Step 2):                                       │
│     (:Airport)-[:ROUTE]->(:Airport)  # Added when schedules loaded         │
│     (:Airline)-[:OPERATES]->(:Route) # Added when schedules loaded         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: CONSUMPTION (Planned for later)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FastAPI:                                                                   │
│  GET /api/airports → SELECT * FROM airports                                │
│  GET /api/airlines → SELECT * FROM airlines                                │
│                                                                              │
│  Dashboard (Streamlit):                                                     │
│  - List airports by country                                                │
│  - List airlines                                                            │
│  - Network map (when routes added in Step 2)                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Object/Class Diagram (Python Data Models)

```
┌─────────────────────────────┐
│      Airport (Dataclass)    │
├─────────────────────────────┤
│ - code: str (PK)            │ 3-letter IATA
│ - name: str                 │ Full airport name
│ - city_code: str            │ 3-letter IATA city code
│ - country_code: str         │ 2-letter ISO country code
│ - latitude: float           │ -90 to +90
│ - longitude: float          │ -180 to +180
│ - timezone: str             │ e.g., "Europe/Berlin"
│ - location_type: str        │ "Airport", "RailwayStation", etc.
│ - is_lh_operated: bool      │ LH operates this airport
│ - loaded_at: datetime       │ When loaded from API
├─────────────────────────────┤
│ + to_dict() → Dict          │
│ + to_csv_row() → List       │
│ + validate() → bool         │
└─────────────────────────────┘


┌─────────────────────────────┐
│      Airline (Dataclass)    │
├─────────────────────────────┤
│ - code: str (PK)            │ 2-letter IATA airline code
│ - name: str                 │ Full airline name
│ - alliance: str (optional)  │ "Star Alliance", "OneWorld", etc.
│ - loaded_at: datetime       │ When loaded from API
├─────────────────────────────┤
│ + to_dict() → Dict          │
│ + to_csv_row() → List       │
│ + validate() → bool         │
└─────────────────────────────┘
```

---

## MongoDB Collection Schema

```
Collection: airports
{
  "_id": "TXL",           // IATA code as ID
  "api_response": {       // FULL raw API response
    "AirportCode": "TXL",
    "Position": {
      "Coordinate": {
        "Latitude": 52.562,
        "Longitude": 13.288
      }
    },
    "CityCode": "BER",
    "CountryCode": "DE",
    "LocationType": "Airport",
    "Names": {
      "Name": [
        {
          "@LanguageCode": "en",
          "$": "Berlin Tegel"
        },
        {
          "@LanguageCode": "de",
          "$": "Berlin Tegel"
        }
      ]
    }
  },
  "fetched_at": ISODate("2024-05-10T12:34:56Z"),
  "city_code": "BER",           // Denormalized for quick filtering
  "country_code": "DE"
}

Collection: airlines
{
  "_id": "LH",            // IATA code as ID
  "api_response": {       // FULL raw API response
    "AirlineCode": "LH",
    "Names": {
      "Name": [
        {
          "@LanguageCode": "en",
          "$": "Lufthansa"
        }
      ]
    }
  },
  "fetched_at": ISODate("2024-05-10T12:34:56Z")
}
```

---

## PostgreSQL Schema (Step 1)

```sql
-- Airports table
CREATE TABLE airports (
  code VARCHAR(3) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  city_code VARCHAR(3),
  country_code VARCHAR(2),
  latitude DECIMAL(10, 6),
  longitude DECIMAL(10, 6),
  timezone VARCHAR(50),
  location_type VARCHAR(50),
  is_lh_operated BOOLEAN DEFAULT FALSE,
  loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_airports_city ON airports(city_code);
CREATE INDEX idx_airports_country ON airports(country_code);

-- Airlines table
CREATE TABLE airlines (
  code VARCHAR(2) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  alliance VARCHAR(50),
  loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Future relationships (Step 2+):
-- ALTER TABLE airports ADD COLUMN hub_airport BOOLEAN DEFAULT FALSE;
-- CREATE TABLE routes (
--   origin_code VARCHAR(3) REFERENCES airports(code),
--   destination_code VARCHAR(3) REFERENCES airports(code),
--   airline_code VARCHAR(2) REFERENCES airlines(code),
--   frequency INT,
--   PRIMARY KEY (origin_code, destination_code, airline_code)
-- );
```

---

## Neo4j Graph Schema (Step 1)

```cypher
// Constraints
CREATE CONSTRAINT airport_code_unique ON (a:Airport) ASSERT a.code IS UNIQUE;
CREATE CONSTRAINT airline_code_unique ON (a:Airline) ASSERT a.code IS UNIQUE;

// Airport Nodes (from airports.csv)
CREATE (airport:Airport {
  code: "TXL",
  name: "Berlin Tegel",
  city_code: "BER",
  country_code: "DE",
  latitude: 52.562,
  longitude: 13.288,
  timezone: "Europe/Berlin",
  is_lh_operated: true
})

// Airline Nodes (from airlines.csv)
CREATE (airline:Airline {
  code: "LH",
  name: "Lufthansa"
})

// Step 2+ Relationships:
// MERGE (origin:Airport {code: "BER"})
// MERGE (dest:Airport {code: "MUC"})
// CREATE (origin)-[:ROUTE {
//   distance_km: 380,
//   frequency: 24
// }]->(dest)

// Future Hub Analysis Query:
// MATCH (a1:Airport)-[:ROUTE]->(a2:Airport)-[:ROUTE]->(a3:Airport)
// RETURN a2.code, count(*) as hub_score
// ORDER BY hub_score DESC
```

---

## Summary: Data Journey

```
                    Raw API Response
                    (Nested JSON)
                          ↓
                    ┌─────────────┐
                    │  MongoDB    │ ← "landing zone" - stores as-is
                    └─────────────┘
                          ↓
                    ┌─────────────────────┐
                    │  Python ETL Layer   │
                    │  (pandas/transformers)
                    └─────────────────────┘
                          ↓
         ┌────────────────┴────────────────┐
         ↓                                  ↓
    ┌─────────────┐                  ┌──────────────┐
    │ PostgreSQL  │                  │   Neo4j      │
    │ (relational)│                  │   (graph)    │
    └─────────────┘                  └──────────────┘
         ↓                                  ↓
    (SQL queries)                   (Cypher queries)
         ↓                                  ↓
    Dashboard, Reports           Network Analysis,
    Aggregations                 Shortest Paths,
    Joins, Grouping              Hub Detection
```

