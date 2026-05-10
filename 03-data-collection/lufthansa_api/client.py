"""Lufthansa API Client"""

import os
from typing import Optional, Dict, Any
from .schemas import Airport, Airline
from .mock_data import get_mock_airports, get_mock_airlines

try:
    import requests
except ImportError:
    requests = None


class LufthansaAPIClient:
    """
    Client for Lufthansa Public API
    Supports both real API calls (with credentials) and mock data for development
    """

    BASE_URL = "https://api.lufthansa.com/v1"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        use_mock: bool = True
    ):
        """
        Initialize the API client

        Args:
            client_id: OAuth2 client ID (from env: LH_CLIENT_ID)
            client_secret: OAuth2 client secret (from env: LH_CLIENT_SECRET)
            use_mock: If True, use mock data instead of real API calls
        """
        self.client_id = client_id or os.getenv("LH_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LH_CLIENT_SECRET")
        self.use_mock = use_mock
        self.token = None

        if not self.use_mock and (not self.client_id or not self.client_secret):
            raise ValueError(
                "Real API mode requires client_id and client_secret. "
                "Provide them as arguments or set LH_CLIENT_ID and LH_CLIENT_SECRET env vars"
            )

    def _authenticate(self):
        """Get OAuth2 token"""
        if self.use_mock:
            return "mock_token"

        if not requests:
            raise ImportError("requests library required for real API mode. Install: pip install requests")

        auth_url = f"{self.BASE_URL}/oauth/token"
        response = requests.post(
            auth_url,
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        return self.token

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API request"""
        if self.use_mock:
            return self._handle_mock_request(endpoint, params)

        if not requests:
            raise ImportError("requests library required for real API mode. Install: pip install requests")

        if not self.token:
            self._authenticate()

        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def _handle_mock_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Route to appropriate mock data based on endpoint"""
        params = params or {}
        limit = int(params.get("limit", 20))
        offset = int(params.get("offset", 0))

        if "airports" in endpoint:
            return get_mock_airports(limit, offset)
        elif "airlines" in endpoint:
            return get_mock_airlines(limit, offset)
        else:
            return {"error": "Unknown endpoint"}

    def get_airports(
        self,
        airport_code: Optional[str] = None,
        lang: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        lh_operated: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get airport reference data

        Args:
            airport_code: 3-letter IATA code (e.g., "TXL"). If None, returns all.
            lang: 2-letter ISO language code
            limit: Number of records (default: 20, max: 100)
            offset: Number of records to skip (default: 0)
            lh_operated: Only LH-operated locations (true/false)

        Returns:
            Response with airport data
        """
        endpoint = f"/references/airports/{airport_code}" if airport_code else "/references/airports"

        params = {
            "limit": limit,
            "offset": offset
        }
        if lang:
            params["lang"] = lang
        if lh_operated is not None:
            params["LHoperated"] = str(int(lh_operated))

        return self._make_request(endpoint, params)

    def get_nearest_airports(
        self,
        latitude: float,
        longitude: float,
        lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get 5 nearest airports to coordinates

        Args:
            latitude: Latitude (-90 to +90)
            longitude: Longitude (-180 to +180)
            lang: 2-letter ISO language code

        Returns:
            Response with 5 nearest airports
        """
        endpoint = f"/references/airports/nearest/{latitude},{longitude}"

        params = {}
        if lang:
            params["lang"] = lang

        return self._make_request(endpoint, params)

    def get_airlines(
        self,
        airline_code: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get airline reference data

        Args:
            airline_code: 2-letter IATA code (e.g., "LH"). If None, returns all.
            limit: Number of records (default: 20, max: 100)
            offset: Number of records to skip (default: 0)

        Returns:
            Response with airline data
        """
        endpoint = f"/references/airlines/{airline_code}" if airline_code else "/references/airlines"

        params = {
            "limit": limit,
            "offset": offset
        }

        return self._make_request(endpoint, params)
