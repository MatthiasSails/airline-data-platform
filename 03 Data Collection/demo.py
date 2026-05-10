"""Demo script - Test the Lufthansa API Client"""

import json
from lufthansa_api.client import LufthansaAPIClient


def demo_mock_mode():
    """Demo with mock data (no credentials needed)"""
    print("=" * 60)
    print("DEMO: Lufthansa API Client (Mock Mode)")
    print("=" * 60)

    client = LufthansaAPIClient(use_mock=True)

    # Get airports
    print("\n1. Getting mock airports...")
    airports_response = client.get_airports(limit=5)
    airports = airports_response.get("ResourceResponse", {}).get("Airport", [])
    print(f"   Found {len(airports)} airports:")
    for airport in airports:
        code = airport.get("AirportCode")
        names = airport.get("Names", {}).get("Name", [])
        name = names[0].get("$") if isinstance(names, list) else names.get("$")
        print(f"     - {code}: {name}")

    # Get airlines
    print("\n2. Getting mock airlines...")
    airlines_response = client.get_airlines(limit=5)
    airlines = airlines_response.get("ResourceResponse", {}).get("Airline", [])
    print(f"   Found {len(airlines)} airlines:")
    for airline in airlines:
        code = airline.get("AirlineCode")
        names = airline.get("Names", {}).get("Name", [])
        name = names[0].get("$") if isinstance(names, list) else names.get("$")
        print(f"     - {code}: {name}")

    # Get specific airport
    print("\n3. Getting specific airport (BER)...")
    response = client.get_airports(airport_code="BER")
    airport = response.get("ResourceResponse", {}).get("Airport", [{}])[0]
    print(f"   Code: {airport.get('AirportCode')}")
    print(f"   City: {airport.get('CityCode')}")
    print(f"   Country: {airport.get('CountryCode')}")
    coord = airport.get("Position", {}).get("Coordinate", {})
    if coord:
        print(f"   Coordinates: {coord.get('Latitude')}, {coord.get('Longitude')}")

    print("\n" + "=" * 60)
    print("✓ Demo completed successfully!")
    print("=" * 60)


def demo_with_real_api():
    """Demo with real API (requires credentials)"""
    print("=" * 60)
    print("DEMO: Lufthansa API Client (Real Mode)")
    print("=" * 60)

    try:
        client = LufthansaAPIClient(use_mock=False)

        print("\nGetting real airport data from LH API...")
        response = client.get_airports(airport_code="BER", limit=1)
        print(json.dumps(response, indent=2))

    except ValueError as e:
        print(f"✗ Error: {e}")
        print("  Set LH_CLIENT_ID and LH_CLIENT_SECRET environment variables")
    except Exception as e:
        print(f"✗ API Error: {e}")


if __name__ == "__main__":
    # Run demo with mock data
    demo_mock_mode()

    print("\n\nTo use with REAL API:")
    print("  1. Set environment variables:")
    print("     export LH_CLIENT_ID='your_client_id'")
    print("     export LH_CLIENT_SECRET='your_client_secret'")
    print("  2. Uncomment demo_with_real_api() below")
    print("  3. Or pass use_mock=False to LufthansaAPIClient()")
