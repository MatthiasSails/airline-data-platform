import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pymongo import MongoClient, errors as mongo_errors

# =============================================================================
# ENVIRONMENT
# Load .env file from same directory as script
# =============================================================================
load_dotenv()

# =============================================================================
# CONFIGURATION
# All constants in one place
# =============================================================================
BASE_URL      = "https://opensky-network.org/api"
BEGIN         = 1778536800
END           = 1778623200
AIRPORT       = "EDDF"
ICAO24        = "3c675a"

RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Bounding box around Germany/Frankfurt (~50 sq° → 2 credits vs 4 for global)
BBOX = {
    "lamin": 47.0,   # south edge
    "lamax": 52.0,   # north edge
    "lomin": 5.0,    # west edge
    "lomax": 15.0,   # east edge
}

# adsb.lol — secondary Bronze-only source (ADR 003/009). No auth required.
# adsb.lol takes a lat/lon/dist (NM) circle rather than a bounding box, so the circle
# and the BBOX can only approximate each other.
#
# dist was 245 NM — the circle *circumscribing* the BBOX (sqrt(150^2 + 194.8^2)). That
# guaranteed full BBOX coverage but pulled ~61% more area than the BBOX asks for, and
# snapshot size scales with aircraft in range: 642 aircraft = 405 KB per document, and at
# the 50s loop that is ~717 MB/day into a 512 MB Atlas cluster — it filled in under a day
# and blocked writes (issue #28).
#
# 150 NM is the *inscribed* circle: it still spans the full 47-52 latitude band but clips
# the eastern/western BBOX corners. Measured on a live snapshot: 282 aircraft = 178 KB,
# ~307 MB/day, which a 24h TTL can hold inside the free tier. Coverage at the lon extremes
# is the deliberate price — see issue #28.
ADSB_BASE_URL = "https://api.adsb.lol/v2"
ADSB_GEO = {
    "lat":  49.5,   # BBOX center latitude
    "lon":  10.0,   # BBOX center longitude
    "dist": 150,    # NM — inscribed in the BBOX (was 245 = circumscribed); see above
}
ADSB_URL = f"{ADSB_BASE_URL}/lat/{ADSB_GEO['lat']}/lon/{ADSB_GEO['lon']}/dist/{ADSB_GEO['dist']}"

# Retention: both raw collections expire documents via a TTL index on fetched_at.
# Changing the value on a live cluster is a collMod, no data loss, no redeploy.
TTL_INDEX_NAME  = "ttl_fetched_at_12h"
TTL_SECONDS     = 1200  # 20 min
TTL_COLLECTIONS = ("states_all", "adsb_raw")

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)


# =============================================================================
# TOKEN MANAGER
# Handles OAuth2 token lifecycle — auto-refreshes before expiry
# =============================================================================
TOKEN_URL            = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
TOKEN_REFRESH_MARGIN = 30  # seconds before expiry to proactively refresh

class TokenManager:
    def __init__(self):
        self.token      = None
        self.expires_at = None

    def get_token(self):
        """Return valid token, refreshing if expired or missing."""
        if self.token and self.expires_at and datetime.now() < self.expires_at:
            return self.token
        return self._refresh()

    def _refresh(self):
        """Fetch a new access token from OpenSky auth server."""
        try:
            r = requests.post(TOKEN_URL, data={
                "grant_type":    "client_credentials",
                "client_id":     os.environ["OPENSKY_CLIENT_ID"],
                "client_secret": os.environ["OPENSKY_CLIENT_SECRET"],
            }, timeout=10)
            r.raise_for_status()
            data            = r.json()
            self.token      = data["access_token"]
            expires_in      = data.get("expires_in", 1800)
            self.expires_at = datetime.now() + timedelta(seconds=expires_in - TOKEN_REFRESH_MARGIN)
            log.info("Token refreshed successfully.")
            return self.token
        except requests.exceptions.HTTPError as e:
            log.error(f"Token refresh failed — HTTP error: {e}")
            raise
        except KeyError as e:
            log.error(f"Missing environment variable: {e}. Ensure OPENSKY_CLIENT_ID and OPENSKY_CLIENT_SECRET are set in .env")
            raise

    def headers(self):
        """Return Authorization header with current valid token."""
        return {"Authorization": f"Bearer {self.get_token()}"}


# =============================================================================
# MONGODB SETUP
# =============================================================================
def get_db():
    """Connect to MongoDB and return the airlines database."""
    try:
        client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=5000)
        # Ping to confirm connection is alive before proceeding
        client.admin.command("ping")
        log.info("MongoDB connection established.")
        return client["airlines"]
    except KeyError:
        log.error("MONGO_URL not set. Ensure it is defined in .env")
        raise
    except mongo_errors.ServerSelectionTimeoutError as e:
        log.error(f"Could not connect to MongoDB: {e}")
        raise


# =============================================================================
# RESPONSE TRANSFORMS
# Applied to a raw API response before it is stored
# =============================================================================
def _in_bbox(lat, lon):
    """True if a position falls inside BBOX. Missing coordinates count as outside."""
    if lat is None or lon is None:
        return False
    return (BBOX["lamin"] <= lat <= BBOX["lamax"]
            and BBOX["lomin"] <= lon <= BBOX["lomax"])


def trim_adsb_to_bbox(data):
    """Drop aircraft outside BBOX from an adsb.lol response before storing.

    This is a guard, not a size optimisation. At the current dist=150 the circle is
    inscribed in the BBOX, so this removes no positioned aircraft at all (measured: 0).
    It earns its place by bounding storage to the BBOX no matter what dist is set to —
    raise dist back toward the circumscribed 245 and roughly 30% of what comes back is
    outside the box, which is how adsb_raw grew until Atlas blocked writes (issue #28).

    It does still drop aircraft with no position fix, which silver skips anyway.
    """
    ac = data.get("ac")
    if not isinstance(ac, list):
        log.warning("adsb response has no 'ac' list — storing unfiltered.")
        return data

    kept = [a for a in ac if _in_bbox(a.get("lat"), a.get("lon"))]
    log.info(f"adsb_raw: kept {len(kept)}/{len(ac)} aircraft inside BBOX.")
    data["ac"] = kept
    return data


# =============================================================================
# DATABASE WRITER
# Inserts with full audit fields for data lineage
# =============================================================================
def save_to_db(db, collection_name, data, pipeline_run_id):
    """
    Insert data into MongoDB with audit fields:
      - fetched_at      : when the API was called
      - load_date       : when the record was written to DB
      - source          : which endpoint the data came from
      - pipeline_run_id : unique ID tying all records from this run together

    fetched_at/load_date are stored as real BSON dates, not ISO strings. A TTL index
    only ever expires a BSON date — pointed at a string it is created without complaint
    and then silently never deletes anything, which is how adsb_raw grew until Atlas
    blocked writes (issue #28). Readers must cope with both types until the historical
    string documents are migrated.

    Uses ordered=False on bulk insert to skip duplicates and continue.
    """
    if not data:
        log.warning(f"No data to insert into '{collection_name}' — skipping.")
        return

    collection = db[collection_name]
    fetched_at = datetime.now(timezone.utc)
    load_date  = datetime.now(timezone.utc)

    try:
        if isinstance(data, list):
            if len(data) == 0:
                log.warning(f"Empty list for '{collection_name}' — skipping.")
                return

            # Stamp every document with audit fields
            docs = [{
                **doc,
                "fetched_at":      fetched_at,
                "load_date":       load_date,
                "source":          collection_name,
                "pipeline_run_id": pipeline_run_id,
            } for doc in data]

            result = collection.insert_many(docs, ordered=False)
            log.info(f"Inserted {len(result.inserted_ids)} documents into '{collection_name}'.")

        elif isinstance(data, dict):
            data.update({
                "fetched_at":      fetched_at,
                "load_date":       load_date,
                "source":          collection_name,
                "pipeline_run_id": pipeline_run_id,
            })
            result = collection.insert_one(data)
            log.info(f"Inserted 1 document into '{collection_name}' (id: {result.inserted_id}).")

        else:
            log.warning(f"Unexpected data type for '{collection_name}': {type(data)} — skipping.")

    except mongo_errors.BulkWriteError as e:
        # Some inserts may fail due to duplicates — log count but don't crash
        write_errors = e.details.get("writeErrors", [])
        log.warning(f"{len(write_errors)} duplicate(s) skipped in '{collection_name}'.")
    except mongo_errors.PyMongoError as e:
        log.error(f"MongoDB insert failed for '{collection_name}': {e}")


# =============================================================================
# CREDIT MONITOR
# =============================================================================
def log_credits(response, name):
    """Read and log rate limit headers from OpenSky response."""
    remaining   = response.headers.get("X-Rate-Limit-Remaining")
    retry_after = response.headers.get("X-Rate-Limit-Retry-After-Seconds")

    if remaining:
        log.info(f"[{name}] Credits remaining: {remaining}")

    if retry_after:
        log.warning(f"[{name}] Rate limited — retry after: {retry_after}s")


# =============================================================================
# CORE FETCH FUNCTION
# Fetches from API then saves to MongoDB
# =============================================================================
def fetch_and_store(name, url, db, pipeline_run_id, params=None, headers=None, transform=None):
    """
    Fetch data from an API endpoint then:
      1. Validate the response
      2. Save to local JSON file inside timestamped run folder
      3. Insert into MongoDB collection with audit fields

    Args:
        name            : collection name and output filename
        url             : full API endpoint URL
        db              : MongoDB database object
        pipeline_run_id : unique ID for this pipeline run
        params          : optional query parameters dict
        headers         : optional request headers; defaults to OpenSky bearer
                           token (pass {} for sources that need no auth, e.g. adsb.lol)
        transform       : optional callable applied to the validated response before
                           storing (e.g. trim_adsb_to_bbox)
    """
    log.info(f"Fetching '{name}' — params={params}")

    try:
        req_headers = headers if headers is not None else tokens.headers()
        r = requests.get(url, params=params, headers=req_headers, timeout=10)

        # Log credits after every call
        log_credits(r, name)

        # Handle known cases explicitly before raise_for_status
        if r.status_code == 404:
            log.warning(f"404 Not Found for '{name}' — no data for given params.")
            return

        if r.status_code == 429:
            retry = r.headers.get("X-Rate-Limit-Retry-After-Seconds", "unknown")
            log.warning(f"429 Rate Limited for '{name}' — retry after {retry}s.")
            return

        # Raises HTTPError for all other 4xx/5xx
        r.raise_for_status()

        # Validate response is parseable JSON
        try:
            data = r.json()
        except ValueError:
            log.error(f"Response for '{name}' is not valid JSON — skipping.")
            return

        # Validate response is not empty
        if data is None or data == [] or data == {}:
            log.warning(f"Empty response for '{name}' — nothing to store.")
            return

        if transform is not None:
            data = transform(data)

        save_to_db(db, name, data, pipeline_run_id)

    except requests.exceptions.ConnectionError:
        log.error(f"Connection error for '{name}' — check internet or API status.")
    except requests.exceptions.Timeout:
        log.error(f"Request timed out for '{name}' — API may be slow.")
    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP error for '{name}': {e}")


# =============================================================================
# MAIN PIPELINE
# =============================================================================
def main():
    pipeline_run_id = f"run_{RUN_TIMESTAMP}"

    log.info("=" * 60)
    log.info(f"PIPELINE START — {pipeline_run_id}")
    log.info("=" * 60)

    db = get_db()

    endpoints = [
        # Bounding box keeps cost at 2 credits instead of 4 for global. The API filters
        # to the BBOX server-side, so no transform is needed here.
        ("states_all", f"{BASE_URL}/states/all", BBOX, None, None),
        # Bronze-only secondary source (ADR 003/009) — no auth. Its circle only
        # approximates the BBOX, so trim the overspill before storing (issue #28).
        ("adsb_raw",   ADSB_URL,                 None, {},   trim_adsb_to_bbox),
    ]

    for name, url, params, headers, transform in endpoints:
        fetch_and_store(name, url, db, pipeline_run_id, params, headers, transform)

    log.info("=" * 60)
    log.info(f"PIPELINE COMPLETE — {pipeline_run_id}")
    log.info("=" * 60)


if __name__ == "__main__":
    tokens = TokenManager()
    main()