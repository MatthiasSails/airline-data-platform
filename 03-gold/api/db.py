import os

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

# Force the asyncpg driver regardless of how the connection string was pasted in —
# plain "postgresql://" (the form Supabase's dashboard copies) makes SQLAlchemy
# default to psycopg2, which this async-only service doesn't install.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    pool_size=2,
    max_overflow=3,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)
