"""Pytest fixtures for async testing with SQLite + aiosqlite.

Provides:
- `async_engine`: Session-scoped async engine using SQLite.
- `create_tables`: Auto-use fixture that creates/drops all tables per session.
- `db_session`: Function-scoped async session that rolls back after each test.
- `client`: Function-scoped async HTTP client with dependency overrides.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import get_db
from app.main import app
from app.models.base import Base

__all__: list[str] = []

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the async backend for tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def async_engine():
    """Create a session-scoped async engine using SQLite for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    return engine


@pytest.fixture(scope="session", autouse=True)
async def create_tables(async_engine: Any) -> AsyncIterator[None]:
    """Create all tables before tests and drop them after.

    This fixture is session-scoped and runs automatically.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await async_engine.dispose()


@pytest.fixture
async def db_session(async_engine: Any) -> AsyncIterator[AsyncSession]:
    """Yield a function-scoped async session that rolls back after each test.

    This ensures test isolation — no test data leaks between test functions.
    """
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Yield an async HTTP client with the test database session injected.

    Overrides the `get_db` dependency to use the test session, then cleans
    up the override after each test.
    """

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
