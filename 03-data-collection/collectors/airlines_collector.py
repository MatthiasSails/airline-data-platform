"""Collect airline reference data from Lufthansa API → PostgreSQL"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lufthansa_api.client import LufthansaAPIClient
from db.postgres.connector import from_env


def collect_airlines(use_mock: bool = True):
    client = LufthansaAPIClient(use_mock=use_mock)

    all_airlines = []
    limit = 100
    offset = 0

    while True:
        response = client.get_airlines(limit=limit, offset=offset)

        if "ResourceResponse" not in response or "Airline" not in response["ResourceResponse"]:
            break

        airlines = response["ResourceResponse"]["Airline"]
        if not airlines:
            break

        all_airlines.extend(airlines)
        offset += limit

        if use_mock and len(all_airlines) >= 5:
            break

    print(f"Fetched {len(all_airlines)} airlines")

    with from_env() as db:
        db.create_tables()
        db.insert_airlines(all_airlines)
        print(f"Inserted {len(all_airlines)} airlines into PostgreSQL")

    return all_airlines


if __name__ == "__main__":
    collect_airlines(use_mock=True)
