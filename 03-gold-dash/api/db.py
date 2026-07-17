import os

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

# Target table for read queries — env-injected so the same image serves prod
# (map1) and the Q stage environment (q_map1). Allowlist-restricted because the
# value is interpolated as a SQL identifier (table names can't be bind params).
MAP_TABLE = os.environ.get("MAP_TABLE", "map1")
if MAP_TABLE not in {"map1", "q_map1"}:
    raise ValueError(f"MAP_TABLE must be 'map1' or 'q_map1', got {MAP_TABLE!r}")

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
