from datetime import datetime

from pydantic import BaseModel


class Aircraft(BaseModel):
    icao24: str | None
    callsign: str | None
    longitude: float | None
    latitude: float | None
    on_ground: bool | None
    true_track: float | None
    vertical_rate: float | None
    updated_at: datetime | None
