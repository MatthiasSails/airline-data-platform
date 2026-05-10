# Architecture Diagrams (Mermaid)

## Data Flow Diagram

```mermaid
graph LR
    API["Lufthansa API<br/>/references/airports<br/>/references/airlines"]
    
    API -->|Raw JSON| Mongo["MongoDB<br/>Landing Zone<br/><br/>db.airports<br/>db.airlines"]
    
    Mongo -->|Extract| ETL["Python ETL<br/>Pandas Transformers<br/><br/>- Extract nested JSON<br/>- Normalize schema<br/>- Validate quality<br/>- Output CSV"]
    
    ETL -->|airports.csv| PG["PostgreSQL<br/>Relational OLAP<br/><br/>airports<br/>airlines<br/>tables"]
    ETL -->|airlines.csv| NEO["Neo4j<br/>Graph DB<br/><br/>Airport nodes<br/>Airline nodes"]
    
    PG -->|SQL queries| DASH["FastAPI + Dashboard<br/><br/>- Airport lookup<br/>- Filter by country<br/>- Aggregate stats"]
    NEO -->|Cypher queries| GRAPH["Graph Visualization<br/><br/>- Network topology<br/>- Hub analysis<br/>- Connectivity"]
    
    style API fill:#4CAF50,color:#fff
    style Mongo fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style PG fill:#0066CC,color:#fff
    style NEO fill:#00AA66,color:#fff
    style DASH fill:#9933CC,color:#fff
    style GRAPH fill:#FF1493,color:#fff
```

---

## Entity Relationship Diagram

```mermaid
erDiagram
    AIRPORT ||--o| AIRLINE : "served by"
    
    AIRPORT {
        string code PK
        string name
        string city_code
        string country_code
        decimal latitude
        decimal longitude
        string timezone
        string location_type
        boolean is_lh_operated
        datetime loaded_at
    }
    
    AIRLINE {
        string code PK
        string name
        string alliance
        datetime loaded_at
    }
```

---

## Layer Architecture

```mermaid
graph TB
    subgraph INGESTION["Layer 1: INGESTION"]
        API["Lufthansa API<br/>OAuth2"]
    end
    
    subgraph STORAGE["Storage: MongoDB"]
        Airports_Collection["db.airports<br/>Raw JSON responses"]
        Airlines_Collection["db.airlines<br/>Raw JSON responses"]
    end
    
    subgraph PROCESSING["Layer 2: PROCESSING<br/>Python ETL"]
        Extract["1. Extract<br/>MongoDB → DataFrame"]
        Transform["2. Transform<br/>Normalize schema"]
        Validate["3. Validate<br/>Data quality"]
        Output["4. Output<br/>CSV files"]
    end
    
    subgraph SERVING["Layer 3: SERVING"]
        PostgreSQL["PostgreSQL<br/>airports table<br/>airlines table"]
        Neo4j["Neo4j<br/>Airport nodes<br/>Airline nodes"]
    end
    
    subgraph CONSUMPTION["Layer 4: CONSUMPTION<br/>Planned Step 4"]
        FastAPI["FastAPI REST API<br/>GET /api/airports<br/>GET /api/airlines"]
        Dashboard["Streamlit Dashboard<br/>Airport search<br/>Filter by country"]
        GraphViz["Graph Visualization<br/>Network topology"]
    end
    
    API --> Airports_Collection
    API --> Airlines_Collection
    
    Airports_Collection --> Extract
    Airlines_Collection --> Extract
    Extract --> Transform
    Transform --> Validate
    Validate --> Output
    
    Output -->|airports.csv| PostgreSQL
    Output -->|airlines.csv| PostgreSQL
    Output -->|airports.csv| Neo4j
    Output -->|airlines.csv| Neo4j
    
    PostgreSQL --> FastAPI
    PostgreSQL --> Dashboard
    Neo4j --> GraphViz
    
    FastAPI --> CONSUMPTION
    Dashboard --> CONSUMPTION
    GraphViz --> CONSUMPTION
    
    style INGESTION fill:#4CAF50,color:#fff
    style STORAGE fill:#FF6B35,color:#fff
    style PROCESSING fill:#FFA500,color:#fff
    style SERVING fill:#0066CC,color:#fff
    style CONSUMPTION fill:#9933CC,color:#fff
```

---

## Processing Pipeline Detail

```mermaid
graph LR
    subgraph RAW["RAW DATA<br/>MongoDB"]
        A["Airport 1<br/>{<br/>  AirportCode: TXL<br/>  Names: {<br/>    Name: [{<br/>      $LanguageCode: en<br/>      $: Berlin Tegel<br/>    }]<br/>  }<br/>  Position: {<br/>    Coordinate: {<br/>      Latitude: 52.562<br/>      Longitude: 13.288<br/>    }<br/>  }<br/>}"]
    end
    
    subgraph TRANSFORM["TRANSFORM<br/>Python"]
        B["Normalize<br/>{<br/>  code: TXL<br/>  name: Berlin Tegel<br/>  latitude: 52.562<br/>  longitude: 13.288<br/>}"]
    end
    
    subgraph OUTPUT["PROCESSED<br/>CSV"]
        C["code,name,latitude,longitude<br/>TXL,Berlin Tegel,52.562,13.288<br/>CDG,Paris CDG,49.009,2.548"]
    end
    
    subgraph LOAD["LOAD<br/>Databases"]
        PG["PostgreSQL<br/>INSERT INTO airports<br/>VALUES(TXL, Berlin Tegel, ...)"]
        NEO["Neo4j<br/>CREATE (:Airport<br/>{code: TXL, ...})"]
    end
    
    A --> B
    B --> C
    C --> PG
    C --> NEO
    
    style RAW fill:#FF6B35,color:#fff
    style TRANSFORM fill:#FFA500,color:#fff
    style OUTPUT fill:#FFEB3B,color:#000
    style LOAD fill:#0066CC,color:#fff
```

---

## MongoDB to PostgreSQL Transformation Example

```mermaid
graph TB
    subgraph MONGO["MongoDB Document"]
        M["<pre>{\n  '_id': 'TXL',\n  'api_response': {\n    'AirportCode': 'TXL',\n    'Names': {\n      'Name': [{\n        '@LanguageCode': 'en',\n        '$': 'Berlin Tegel'\n      }]\n    },\n    'Position': {\n      'Coordinate': {\n        'Latitude': 52.562,\n        'Longitude': 13.288\n      }\n    },\n    'CityCode': 'BER',\n    'CountryCode': 'DE'\n  },\n  'fetched_at': ISODate('...')\n}</pre>"]
    end
    
    subgraph CSV["CSV Row"]
        C["code|name|city_code|country_code|latitude|longitude|...<br/>TXL|Berlin Tegel|BER|DE|52.562|13.288|..."]
    end
    
    subgraph PGSQL["PostgreSQL Row"]
        P["code='TXL'<br/>name='Berlin Tegel'<br/>city_code='BER'<br/>country_code='DE'<br/>latitude=52.562<br/>longitude=13.288"]
    end
    
    M -->|Extract + Flatten| C
    C -->|Parse| P
    
    style MONGO fill:#FF6B35,color:#fff
    style CSV fill:#FFEB3B,color:#000
    style PGSQL fill:#0066CC,color:#fff
```

---

## Neo4j Query Examples (Step 1 & Future)

```mermaid
graph TB
    subgraph STEP1["Step 1: Reference Data"]
        Q1["Query: All Airports<br/>MATCH (a:Airport)<br/>RETURN a.code, a.name<br/><br/>Result:<br/>BER, Berlin Brandenburg<br/>TXL, Berlin Tegel<br/>CDG, Paris CDG"]
        Q2["Query: All Airlines<br/>MATCH (a:Airline)<br/>RETURN a.code, a.name<br/><br/>Result:<br/>LH, Lufthansa<br/>BA, British Airways"]
    end
    
    subgraph STEP2["Step 2+: Routes (Future)"]
        Q3["Query: Airport Connectivity<br/>MATCH (a1:Airport)<br/>  -[:ROUTE]->(a2:Airport)<br/>RETURN a1.code, a2.code<br/><br/>Result:<br/>BER → MUC<br/>BER → CDG"]
        Q4["Query: Find Hubs<br/>MATCH (a1:Airport)<br/>  -[:ROUTE]->(hub:Airport)<br/>  -[:ROUTE]->(a3:Airport)<br/>RETURN hub.code, count(*)<br/>ORDER BY count(*) DESC<br/><br/>Result:<br/>FRA: 48 connections<br/>MUC: 42 connections"]
    end
    
    style STEP1 fill:#00AA66,color:#fff
    style STEP2 fill:#FF9800,color:#fff
```

---

## File Dependencies

```mermaid
graph TD
    API["Lufthansa API<br/>lufthansa_api/client.py"]
    
    API --> COLLECTORS["Collectors<br/>collectors/airports_collector.py<br/>collectors/airlines_collector.py"]
    
    COLLECTORS -->|Calls| CLIENT["LufthansaAPIClient<br/>use_mock=True/False"]
    
    COLLECTORS -->|Output| JSON_DATA["JSON Files<br/>data/airports.json<br/>data/airlines.json"]
    
    JSON_DATA --> ETL["Processing<br/>processing/transformers.py<br/>processing/validators.py"]
    
    ETL -->|Output| CSV_DATA["CSV Files<br/>data/airports.csv<br/>data/airlines.csv"]
    
    CSV_DATA --> PG_LOADER["PostgreSQL Loader<br/>processing/postgres_loader.py"]
    CSV_DATA --> NEO_LOADER["Neo4j Loader<br/>processing/neo4j_loader.py"]
    
    PG_LOADER -->|Uses| PG_SCHEMA["PostgreSQL Schema<br/>schemas/postgres_schema.sql"]
    NEO_LOADER -->|Uses| NEO_SCHEMA["Neo4j Schema<br/>schemas/neo4j_schema.cypher"]
    
    PG_LOADER --> PG["PostgreSQL DB<br/>tables: airports, airlines"]
    NEO_LOADER --> NEO["Neo4j DB<br/>nodes: Airport, Airline"]
    
    PG --> API_SERVER["FastAPI<br/>GET /api/airports<br/>GET /api/airlines"]
    NEO --> GRAPH["Graph Visualization"]
    
    style API fill:#4CAF50,color:#fff
    style COLLECTORS fill:#0066CC,color:#fff
    style CLIENT fill:#0066CC,color:#fff
    style JSON_DATA fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style CSV_DATA fill:#FFEB3B,color:#000
    style PG_LOADER fill:#0066CC,color:#fff
    style NEO_LOADER fill:#00AA66,color:#fff
    style PG_SCHEMA fill:#0066CC,color:#fff
    style NEO_SCHEMA fill:#00AA66,color:#fff
    style PG fill:#0066CC,color:#fff
    style NEO fill:#00AA66,color:#fff
    style API_SERVER fill:#9933CC,color:#fff
    style GRAPH fill:#FF1493,color:#fff
```

