"""User repository — extends BaseRepository with user-specific queries."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository

__all__: list[str] = ["UserRepository"]


class UserRepository(BaseRepository[User]):
    """Repository for User model operations.

    Provides additional lookup methods beyond the generic CRUD in
    BaseRepository.
    """

    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by their email address.

        Args:
            email: The email address to search for.

        Returns:
            The User instance, or None if not found.
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by their username.

        Args:
            username: The username to search for.

        Returns:
            The User instance, or None if not found.
        """
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """Fetch a paginated list of active users.

        Args:
            offset: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (active_users, total_active_count).
        """
        base_filter = User.is_active.is_(True)

        count_stmt = select(func.count()).select_from(User).where(base_filter)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = select(User).where(base_filter).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total
