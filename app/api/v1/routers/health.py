"""Health check endpoint.

Reports application and database health status with response time
measurements for each component check.
"""

import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.logging import get_logger, request_id_ctx_var
from app.database import get_db

__all__: list[str] = ["router"]

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/health",
    summary="Health check",
    description="Returns the health status of the application and its dependencies.",
    response_description="Health status report with component-level details.",
)
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Perform a comprehensive health check.

    Checks:
        1. Application is running (always passes).
        2. Database connectivity via `SELECT 1`.
        3. Reports overall status: healthy, degraded, or unhealthy.
        4. Includes response time in ms for each check.

    Returns:
        HTTP 200 if healthy or degraded, HTTP 503 if unhealthy.
    """
    checks: list[dict[str, Any]] = []
    overall_status = "healthy"

    # ── Application check (always passes) ────────────────────
    app_start = time.perf_counter()
    checks.append({
        "name": "application",
        "status": "healthy",
        "duration_ms": round((time.perf_counter() - app_start) * 1000, 2),
    })

    # ── Database connectivity check ──────────────────────────
    db_start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as exc:
        logger.warning("health_check_db_failed", error=str(exc))
        db_status = "unhealthy"
        overall_status = "degraded"

    checks.append({
        "name": "database",
        "status": db_status,
        "duration_ms": round((time.perf_counter() - db_start) * 1000, 2),
    })

    # ── Determine overall status ─────────────────────────────
    if any(check["status"] == "unhealthy" for check in checks):
        overall_status = "degraded"

    # If ALL checks are unhealthy, the system is truly unhealthy
    if all(check["status"] == "unhealthy" for check in checks if check["name"] != "application"):
        overall_status = "unhealthy"

    status_code = 503 if overall_status == "unhealthy" else 200

    body: dict[str, Any] = {
        "success": overall_status != "unhealthy",
        "data": {
            "status": overall_status,
            "checks": checks,
            "version": "0.1.0",
        },
        "message": f"System is {overall_status}",
        "errors": None,
        "request_id": request_id_ctx_var.get(""),
    }

    return JSONResponse(status_code=status_code, content=body)
