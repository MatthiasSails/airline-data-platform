"""Collect airport reference data from Lufthansa API"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lufthansa_api.client import LufthansaAPIClient


def collect_airports(output_file: str = "data/airports.json", use_mock: bool = True):
    """
    Collect airport data from Lufthansa API

    Args:
        output_file: Where to save the JSON data
        use_mock: If True, use mock data instead of real API
    """
    print(f"Collecting airport data (use_mock={use_mock})...")

    client = LufthansaAPIClient(use_mock=use_mock)

    try:
        # Get all airports (using pagination)
        all_airports = []
        limit = 100  # Max allowed
        offset = 0

        while True:
            print(f"  Fetching airports: offset={offset}, limit={limit}")

            response = client.get_airports(limit=limit, offset=offset)

            if "ResourceResponse" not in response or "Airport" not in response["ResourceResponse"]:
                print("  No more airports")
                break

            airports = response["ResourceResponse"]["Airport"]
            if not airports:
                break

            all_airports.extend(airports)
            offset += limit

            # Safety limit for mock data
            if use_mock and len(all_airports) >= 5:
                break

        print(f"  ✓ Collected {len(all_airports)} airports")

        # Save to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump({"airports": all_airports}, f, indent=2)

        print(f"  ✓ Saved to {output_file}")

        return all_airports

    except Exception as e:
        print(f"  ✗ Error: {e}")
        raise


if __name__ == "__main__":
    # Example usage with mock data
    airports = collect_airports(use_mock=True)
    for airport in airports[:3]:
        code = airport.get("AirportCode")
        name = airport.get("Names", {}).get("Name")
        print(f"    {code}: {name}")
