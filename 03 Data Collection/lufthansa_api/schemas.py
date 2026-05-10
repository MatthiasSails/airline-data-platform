"""Data models for Lufthansa API responses"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Coordinate:
    """Geographic coordinate"""
    latitude: float
    longitude: float


@dataclass
class Airport:
    """Airport reference data"""
    code: str  # 3-letter IATA code (e.g., "TXL")
    city_code: Optional[str] = None  # 3-letter IATA city code
    country_code: Optional[str] = None  # 2-letter ISO country code
    name: Optional[str] = None
    location_type: Optional[str] = None  # "Airport", "RailwayStation", "BusStation"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def to_dict(self):
        return {
            "AirportCode": self.code,
            "CityCode": self.city_code,
            "CountryCode": self.country_code,
            "Names": {"Name": self.name} if self.name else None,
            "LocationType": self.location_type,
            "Position": {
                "Coordinate": {
                    "Latitude": self.latitude,
                    "Longitude": self.longitude
                }
            } if self.latitude and self.longitude else None
        }


@dataclass
class Airline:
    """Airline reference data"""
    code: str  # 2-letter IATA airline code (e.g., "LH")
    name: Optional[str] = None

    def to_dict(self):
        return {
            "AirlineCode": self.code,
            "AirlineName": self.name
        }
