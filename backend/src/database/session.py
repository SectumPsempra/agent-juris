from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

connect_args = {}

# Disable prepared statement cache for PostgreSQL to ensure compatibility with
# connection poolers like PgBouncer or RDS Proxy (common in managed environments).
if "postgresql" in settings.database_url:
    connect_args["prepared_statement_cache_size"] = 0

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
    # Verifies connection health before use to prevent "connection lost" errors
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    import src.database.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(src.database.models.Base.metadata.create_all)
