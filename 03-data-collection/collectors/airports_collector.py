"""Collect airport reference data from Lufthansa API → PostgreSQL"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lufthansa_api.client import LufthansaAPIClient
from db.postgres.connector import from_env


def collect_airports(use_mock: bool = True):
    client = LufthansaAPIClient(use_mock=use_mock)

    all_airports = []
    limit = 100
    offset = 0

    while True:
        response = client.get_airports(limit=limit, offset=offset)

        if "ResourceResponse" not in response or "Airport" not in response["ResourceResponse"]:
            break

        airports = response["ResourceResponse"]["Airport"]
        if not airports:
            break

        all_airports.extend(airports)
        offset += limit

        if use_mock and len(all_airports) >= 5:
            break

    print(f"Fetched {len(all_airports)} airports")

    with from_env() as db:
        db.create_tables()
        db.insert_airports(all_airports)
        print(f"Inserted {len(all_airports)} airports into PostgreSQL")

    return all_airports


if __name__ == "__main__":
    collect_airports(use_mock=True)
