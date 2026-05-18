"""OpenSky Network API Client"""

import os
from typing import Optional
from dotenv import load_dotenv
from .mock_data import get_mock_departures, get_mock_arrivals

try:
    import requests
except ImportError:
    requests = None


class OpenSkyClient:
    """
    Client for OpenSky Network API.
    Supports real API (OAuth2) and mock mode for development.
    """

    TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    BASE_URL = "https://opensky-network.org/api"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        use_mock: bool = True
    ):
        load_dotenv(override=True)
        self.client_id = client_id or os.getenv("OPENSKY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("OPENSKY_CLIENT_SECRET")
        self.use_mock = use_mock
        self._token = None

    def _authenticate(self) -> str:
        if self.use_mock:
            return "mock_token"

        if not requests:
            raise ImportError("requests library required. Run: pip install requests")

        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]
        return self._token

    def _make_request(self, endpoint: str, params: dict) -> list:
        if self.use_mock:
            return self._handle_mock(endpoint, params)

        if not self._token:
            self._authenticate()

        response = requests.get(
            f"{self.BASE_URL}{endpoint}",
            params=params,
            headers={"Authorization": f"Bearer {self._token}"}
        )
        # OpenSky returns 404 when no flights exist for the given window — treat as empty
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()

    def _handle_mock(self, endpoint: str, params: dict) -> list:
        airport = params.get("airport", "EDDB")
        if "departure" in endpoint:
            return get_mock_departures(airport)
        elif "arrival" in endpoint:
            return get_mock_arrivals(airport)
        return []

    def get_departures(self, airport: str, begin: int, end: int) -> list:
        """
        Get flights that departed from airport in time window.

        Args:
            airport: ICAO code, e.g. "EDDB" (Berlin Brandenburg)
            begin: Unix timestamp start
            end: Unix timestamp end (max 7 days after begin)
        """
        return self._make_request(
            "/flights/departure",
            {"airport": airport, "begin": begin, "end": end}
        )

    def get_arrivals(self, airport: str, begin: int, end: int) -> list:
        """
        Get flights that arrived at airport in time window.

        Args:
            airport: ICAO code, e.g. "EDDB"
            begin: Unix timestamp start
            end: Unix timestamp end (max 7 days after begin)
        """
        return self._make_request(
            "/flights/arrival",
            {"airport": airport, "begin": begin, "end": end}
        )

    def get_flights_by_aircraft(self, icao24: str, begin: int, end: int) -> list:
        """
        Get all flights for a specific aircraft.

        Args:
            icao24: Aircraft transponder address, e.g. "3c56f0"
            begin: Unix timestamp start
            end: Unix timestamp end (max 30 days after begin)
        """
        return self._make_request(
            "/flights/aircraft",
            {"icao24": icao24, "begin": begin, "end": end}
        )
