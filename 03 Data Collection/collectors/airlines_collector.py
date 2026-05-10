"""Collect airline reference data from Lufthansa API"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lufthansa_api.client import LufthansaAPIClient


def collect_airlines(output_file: str = "data/airlines.json", use_mock: bool = True):
    """
    Collect airline data from Lufthansa API

    Args:
        output_file: Where to save the JSON data
        use_mock: If True, use mock data instead of real API
    """
    print(f"Collecting airline data (use_mock={use_mock})...")

    client = LufthansaAPIClient(use_mock=use_mock)

    try:
        # Get all airlines (using pagination)
        all_airlines = []
        limit = 100  # Max allowed
        offset = 0

        while True:
            print(f"  Fetching airlines: offset={offset}, limit={limit}")

            response = client.get_airlines(limit=limit, offset=offset)

            if "ResourceResponse" not in response or "Airline" not in response["ResourceResponse"]:
                print("  No more airlines")
                break

            airlines = response["ResourceResponse"]["Airline"]
            if not airlines:
                break

            all_airlines.extend(airlines)
            offset += limit

            # Safety limit for mock data
            if use_mock and len(all_airlines) >= 5:
                break

        print(f"  ✓ Collected {len(all_airlines)} airlines")

        # Save to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump({"airlines": all_airlines}, f, indent=2)

        print(f"  ✓ Saved to {output_file}")

        return all_airlines

    except Exception as e:
        print(f"  ✗ Error: {e}")
        raise


if __name__ == "__main__":
    # Example usage with mock data
    airlines = collect_airlines(use_mock=True)
    for airline in airlines[:3]:
        code = airline.get("AirlineCode")
        names = airline.get("Names", {}).get("Name")
        name = names[0]["$"] if isinstance(names, list) else names.get("$")
        print(f"    {code}: {name}")
