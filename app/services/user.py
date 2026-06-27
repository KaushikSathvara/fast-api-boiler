"""User service — business logic over UserRepository.

Handles uniqueness checks, password hashing, and response mapping.
This is the only layer allowed to call UserRepository methods.
"""

from uuid import UUID

from app.config import Settings
from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.schemas.base import PageParams, PaginatedResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__: list[str] = ["UserService"]


class UserService:
    """Service for user-related business logic.

    Orchestrates between UserRepository and Pydantic schemas, enforcing
    business rules such as uniqueness constraints and password hashing.
    """

    def __init__(self, repo: UserRepository, settings: Settings) -> None:
        self.repo = repo
        self.settings = settings

    async def create_user(self, data: UserCreate) -> UserRead:
        """Create a new user after checking email/username uniqueness.

        Args:
            data: Validated UserCreate schema.

        Returns:
            The created user as a UserRead schema.

        Raises:
            ConflictError: If the email or username is already taken.
        """
        # Check email uniqueness
        existing_email = await self.repo.get_by_email(data.email)
        if existing_email is not None:
            raise ConflictError(
                message=f"User with email '{data.email}' already exists",
                detail={"field": "email", "value": data.email},
            )

        # Check username uniqueness
        existing_username = await self.repo.get_by_username(data.username)
        if existing_username is not None:
            raise ConflictError(
                message=f"User with username '{data.username}' already exists",
                detail={"field": "username", "value": data.username},
            )

        # Hash the password before storing
        hashed = hash_password(data.password)

        # Build a schema-like object with hashed_password instead of password
        from pydantic import BaseModel

        class _UserCreateInternal(BaseModel):
            email: str
            username: str
            hashed_password: str

        internal_data = _UserCreateInternal(
            email=data.email,
            username=data.username,
            hashed_password=hashed,
        )

        user = await self.repo.create(internal_data)
        return UserRead.model_validate(user)

    async def get_user(self, id: UUID) -> UserRead:  # noqa: A002
        """Fetch a user by ID.

        Args:
            id: The UUID of the user.

        Returns:
            The user as a UserRead schema.

        Raises:
            NotFoundError: If the user does not exist.
        """
        user = await self.repo.get_or_raise(id)
        return UserRead.model_validate(user)

    async def list_users(self, params: PageParams) -> PaginatedResponse[UserRead]:
        """List users with pagination.

        Args:
            params: Pagination parameters (page, page_size).

        Returns:
            A paginated response containing UserRead items.
        """
        users, total = await self.repo.list(
            offset=params.offset,
            limit=params.page_size,
        )
        items = [UserRead.model_validate(user) for user in users]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def update_user(self, id: UUID, data: UserUpdate) -> UserRead:  # noqa: A002
        """Update a user with partial data.

        Re-hashes the password if it is included in the update.

        Args:
            id: The UUID of the user to update.
            data: Validated UserUpdate schema (only set fields are applied).

        Returns:
            The updated user as a UserRead schema.

        Raises:
            NotFoundError: If the user does not exist.
            ConflictError: If the new email or username is already taken.
        """
        # Check uniqueness for email if provided
        if data.email is not None:
            existing = await self.repo.get_by_email(data.email)
            if existing is not None and existing.id != id:
                raise ConflictError(
                    message=f"User with email '{data.email}' already exists",
                    detail={"field": "email", "value": data.email},
                )

        # Check uniqueness for username if provided
        if data.username is not None:
            existing = await self.repo.get_by_username(data.username)
            if existing is not None and existing.id != id:
                raise ConflictError(
                    message=f"User with username '{data.username}' already exists",
                    detail={"field": "username", "value": data.username},
                )

        # If password is being updated, hash it and replace in update data
        if data.password is not None:
            from pydantic import BaseModel

            update_dict = data.model_dump(exclude_unset=True)
            update_dict.pop("password")
            update_dict["hashed_password"] = hash_password(data.password)

            class _UserUpdateInternal(BaseModel):
                email: str | None = None
                username: str | None = None
                hashed_password: str | None = None
                is_active: bool | None = None

            internal_data = _UserUpdateInternal(**update_dict)
            user = await self.repo.update(id, internal_data)
        else:
            user = await self.repo.update(id, data)

        return UserRead.model_validate(user)

    async def delete_user(self, id: UUID) -> None:  # noqa: A002
        """Delete a user by ID.

        Args:
            id: The UUID of the user to delete.

        Raises:
            NotFoundError: If the user does not exist.
        """
        await self.repo.delete(id)
