from fastapi import APIRouter
from sqlalchemy import text

from db import async_session, MAP_TABLE
from models import Aircraft

router = APIRouter()

# MAP_TABLE is allowlist-validated in db.py, so this f-string interpolation is injection-safe.
CURRENT_AIRCRAFT_QUERY = text(
    f"""
    SELECT icao24, callsign, longitude, latitude, on_ground, true_track, vertical_rate, updated_at
    FROM {MAP_TABLE}
    WHERE longitude IS NOT NULL AND latitude IS NOT NULL
    """
)


@router.get("/aircraft/current", response_model=list[Aircraft])
async def get_current_aircraft() -> list[Aircraft]:
    async with async_session() as session:
        result = await session.execute(CURRENT_AIRCRAFT_QUERY)
        rows = result.mappings().all()
    return [Aircraft(**row) for row in rows]
