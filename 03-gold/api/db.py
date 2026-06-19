import os

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    pool_size=2,
    max_overflow=3,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)
