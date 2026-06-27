"""Async database engine, session factory, and lifecycle hooks.

Only `main.py` and `alembic/env.py` should import `engine` directly.
All other modules should use `get_db()` via dependency injection.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.core.logging import get_logger

__all__: list[str] = ["engine", "async_session_factory", "get_db", "init_db", "close_db"]

settings = get_settings()
logger = get_logger(__name__)

engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DATABASE_ECHO,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async database session.

    Commits on success, rolls back on exception, and always closes the session.
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Verify database connectivity on startup."""
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1"),
            )
        logger.info("database_connection_established", url=str(settings.DATABASE_URL).split("@")[-1])
    except Exception as exc:
        logger.error("database_connection_failed", error=str(exc))
        raise


async def close_db() -> None:
    """Dispose of the database engine on shutdown."""
    await engine.dispose()
    logger.info("database_engine_disposed")
