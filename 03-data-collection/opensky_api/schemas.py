"""Data models for OpenSky API responses"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Flight:
    """A flight as returned by the OpenSky API"""
    icao24: str                              # Aircraft transponder address
    callsign: Optional[str]                  # e.g. "EWG1R"
    first_seen: int                          # Unix timestamp departure
    last_seen: int                           # Unix timestamp arrival
    departure_airport: Optional[str]         # ICAO code, e.g. "EDDB"
    arrival_airport: Optional[str]           # ICAO code, e.g. "EDDM"
    departure_horiz_distance: Optional[int]  # meters to departure airport
    arrival_horiz_distance: Optional[int]    # meters to arrival airport
