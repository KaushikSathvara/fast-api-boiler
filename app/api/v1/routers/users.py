"""User CRUD endpoints.

All endpoints return `APIResponse[...]` envelopes and use dependency injection
for database sessions and application settings.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.logging import request_id_ctx_var
from app.database import get_db
from app.repositories.user import UserRepository
from app.schemas.base import APIResponse, PageParams, PaginatedResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user import UserService

__all__: list[str] = ["router"]

router = APIRouter()


def _get_user_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserService:
    """Factory for UserService with injected dependencies."""
    repo = UserRepository(db)
    return UserService(repo, settings)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Register a new user account with email, username, and password.",
    response_description="The newly created user.",
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "Email or username already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_user(
    data: UserCreate,
    service: Annotated[UserService, Depends(_get_user_service)],
) -> APIResponse[UserRead]:
    """Create a new user."""
    user = await service.create_user(data)
    return APIResponse(
        success=True,
        data=user,
        message="User created successfully",
        request_id=request_id_ctx_var.get(""),
    )


@router.get(
    "",
    summary="List users",
    description="Retrieve a paginated list of all users.",
    response_description="Paginated list of users.",
    responses={
        200: {"description": "Users retrieved successfully"},
    },
)
async def list_users(
    service: Annotated[UserService, Depends(_get_user_service)],
    params: Annotated[PageParams, Depends()],
) -> APIResponse[PaginatedResponse[UserRead]]:
    """List users with pagination."""
    paginated = await service.list_users(params)
    return APIResponse(
        success=True,
        data=paginated,
        message="Users retrieved successfully",
        request_id=request_id_ctx_var.get(""),
    )


@router.get(
    "/{user_id}",
    summary="Get a user",
    description="Retrieve a single user by their unique identifier.",
    response_description="The requested user.",
    responses={
        200: {"description": "User retrieved successfully"},
        404: {"description": "User not found"},
    },
)
async def get_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(_get_user_service)],
) -> APIResponse[UserRead]:
    """Get a user by ID."""
    user = await service.get_user(user_id)
    return APIResponse(
        success=True,
        data=user,
        message="User retrieved successfully",
        request_id=request_id_ctx_var.get(""),
    )


@router.patch(
    "/{user_id}",
    summary="Update a user",
    description="Partially update a user's information. Only provided fields are updated.",
    response_description="The updated user.",
    responses={
        200: {"description": "User updated successfully"},
        404: {"description": "User not found"},
        409: {"description": "Email or username already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    service: Annotated[UserService, Depends(_get_user_service)],
) -> APIResponse[UserRead]:
    """Update a user by ID with partial data."""
    user = await service.update_user(user_id, data)
    return APIResponse(
        success=True,
        data=user,
        message="User updated successfully",
        request_id=request_id_ctx_var.get(""),
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description="Permanently delete a user account by their unique identifier.",
    response_description="No content.",
    responses={
        204: {"description": "User deleted successfully"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(_get_user_service)],
) -> None:
    """Delete a user by ID."""
    await service.delete_user(user_id)
