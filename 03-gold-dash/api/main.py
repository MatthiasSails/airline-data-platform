from fastapi import FastAPI
from sqlalchemy import text

from db import engine
from routers.aircraft import router as aircraft_router

app = FastAPI(title="Frankfurt OpenSky API")
app.include_router(aircraft_router)


@app.get("/health")
async def health() -> dict[str, str]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
