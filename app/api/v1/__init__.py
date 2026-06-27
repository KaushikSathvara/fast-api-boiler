"""API v1 package."""

from fastapi import APIRouter

from app.api.v1.routers import health, users

__all__: list[str] = ["router"]

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
