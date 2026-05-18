"""MongoDB connector for the Airline Data Engineering project — Phase 2 Landing Zone"""

import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


class MongoConnector:

    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self._client: MongoClient | None = None

    def connect(self) -> "MongoConnector":
        self._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
        # Fail fast if the server is unreachable
        self._client.admin.command("ping")
        logger.info("MongoDB connected: %s / %s", self.uri, self.db_name)
        return self

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "MongoConnector":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def collection(self, name: str) -> Collection:
        if self._client is None:
            raise RuntimeError("Not connected — use 'with MongoConnector(...) as db'")
        return self._client[self.db_name][name]

    def insert_raw(self, collection_name: str, document: dict) -> str:
        """Insert one raw API document into any collection. Returns the inserted _id."""
        col = self.collection(collection_name)
        result = col.insert_one(document)
        logger.debug("Inserted document _id=%s into %s", result.inserted_id, collection_name)
        return str(result.inserted_id)

    def insert_adsb_snapshot(self, collection_name: str, snapshot: dict) -> str:
        """Insert one raw adsb.lol API snapshot. Returns the inserted _id."""
        col = self.collection(collection_name)
        result = col.insert_one(snapshot)
        logger.debug("Inserted snapshot _id=%s (%d aircraft)", result.inserted_id, len(snapshot.get("ac", [])))
        return str(result.inserted_id)


def from_env() -> MongoConnector:
    """Create connector from .env / environment variables."""
    load_dotenv(override=True)
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "airline_landing")
    return MongoConnector(uri=uri, db_name=db_name)
