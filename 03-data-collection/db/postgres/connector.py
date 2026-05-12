"""PostgreSQL connector for the Airline Data Engineering project"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv


class PostgresConnector:

    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )
        self.cursor = self.connection.cursor()
        return self

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.close()

    def create_tables(self):
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            self.cursor.execute(f.read())
        self.connection.commit()

    def insert_airports(self, airports: list):
        for airport in airports:
            code = airport.get("AirportCode")
            names = airport.get("Names", {}).get("Name", [])
            name = names[0].get("$") if isinstance(names, list) and names else None
            city_code = airport.get("CityCode")
            country_code = airport.get("CountryCode")
            coordinate = airport.get("Position", {}).get("Coordinate", {})
            latitude = coordinate.get("Latitude")
            longitude = coordinate.get("Longitude")

            self.cursor.execute("""
                INSERT INTO airports (code, name, city_code, country_code, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name         = EXCLUDED.name,
                    city_code    = EXCLUDED.city_code,
                    country_code = EXCLUDED.country_code,
                    latitude     = EXCLUDED.latitude,
                    longitude    = EXCLUDED.longitude
            """, (code, name, city_code, country_code, latitude, longitude))

        self.connection.commit()

    def insert_airlines(self, airlines: list):
        for airline in airlines:
            code = airline.get("AirlineCode")
            names = airline.get("Names", {}).get("Name", [])
            name = names[0].get("$") if isinstance(names, list) and names else None

            self.cursor.execute("""
                INSERT INTO airlines (code, name)
                VALUES (%s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name
            """, (code, name))

        self.connection.commit()


def from_env():
    """Create connector from .env file"""
    load_dotenv()
    return PostgresConnector(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
