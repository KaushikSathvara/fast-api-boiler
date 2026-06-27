"""Tests for the /health endpoint.

Verifies that the health check returns proper status, response keys,
and database connectivity reporting.
"""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.config import get_settings

settings = get_settings()
HEALTH_URL = f"{settings.API_V1_PREFIX}/health"


async def test_health_returns_200(client: AsyncClient) -> None:
    """Health check should return HTTP 200 when all systems are operational."""
    response = await client.get(HEALTH_URL)
    assert response.status_code == 200


async def test_health_response_has_required_keys(client: AsyncClient) -> None:
    """Health response must include status, checks, and version keys."""
    response = await client.get(HEALTH_URL)
    body = response.json()

    assert "success" in body
    assert "data" in body
    assert body["data"] is not None

    data = body["data"]
    assert "status" in data
    assert "checks" in data
    assert "version" in data


async def test_health_db_check_passes_with_valid_connection(client: AsyncClient) -> None:
    """Database check should report 'healthy' with a valid connection."""
    response = await client.get(HEALTH_URL)
    body = response.json()

    db_check = next(
        (check for check in body["data"]["checks"] if check["name"] == "database"),
        None,
    )
    assert db_check is not None
    assert db_check["status"] == "healthy"
    assert "duration_ms" in db_check


async def test_health_db_check_shows_degraded_when_db_unreachable(
    client: AsyncClient,
) -> None:
    """Database check should report degraded when the DB is unreachable."""
    mock_execute = AsyncMock(side_effect=ConnectionError("DB unreachable"))

    with patch(
        "app.api.v1.routers.health.AsyncSession.execute",
        mock_execute,
        create=True,
    ):
        response = await client.get(HEALTH_URL)

    body = response.json()
    # When DB is unreachable, overall status should be degraded or unhealthy
    assert body["data"]["status"] in ("degraded", "unhealthy")
