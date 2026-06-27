"""Generic base repository with typed CRUD and pagination.

Provides a `BaseRepository[ModelT]` that implements get, get_or_raise,
list (with pagination), create, update, delete, and exists operations.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.base import Base

__all__: list[str] = ["BaseRepository", "ModelT", "CreateSchemaT", "UpdateSchemaT"]

ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """Generic repository providing typed CRUD operations.

    Subclasses must set the `model` class variable to the SQLAlchemy model
    they operate on.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: UUID) -> ModelT | None:  # noqa: A002
        """Fetch a single record by primary key.

        Args:
            id: The UUID primary key.

        Returns:
            The model instance, or None if not found.
        """
        stmt = select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_raise(self, id: UUID) -> ModelT:  # noqa: A002
        """Fetch a single record by primary key, or raise NotFoundError.

        Args:
            id: The UUID primary key.

        Returns:
            The model instance.

        Raises:
            NotFoundError: If the record does not exist.
        """
        instance = await self.get(id)
        if instance is None:
            raise NotFoundError(
                message=f"{self.model.__name__} with id '{id}' not found",
                detail={"id": str(id)},
            )
        return instance

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        """Fetch a paginated list of records with an optional filter.

        Args:
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            filters: Optional dict of column_name=value equality filters.

        Returns:
            A tuple of (items, total_count).
        """
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if filters:
            for column_name, value in filters.items():
                column = getattr(self.model, column_name, None)
                if column is not None:
                    stmt = stmt.where(column == value)
                    count_stmt = count_stmt.where(column == value)

        # Execute count query
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Execute data query
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, data: CreateSchemaT) -> ModelT:
        """Create a new record from a Pydantic schema.

        Args:
            data: Pydantic schema with creation data.

        Returns:
            The newly created model instance.
        """
        instance = self.model(**data.model_dump(exclude_unset=True))
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, data: UpdateSchemaT) -> ModelT:  # noqa: A002
        """Update an existing record with partial data.

        Args:
            id: The UUID primary key of the record to update.
            data: Pydantic schema with update data (only set fields are applied).

        Returns:
            The updated model instance.

        Raises:
            NotFoundError: If the record does not exist.
        """
        instance = await self.get_or_raise(id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(instance, field, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> None:  # noqa: A002
        """Delete a record by primary key.

        Args:
            id: The UUID primary key of the record to delete.

        Raises:
            NotFoundError: If the record does not exist.
        """
        instance = await self.get_or_raise(id)
        await self.session.delete(instance)
        await self.session.flush()

    async def exists(self, **kwargs: Any) -> bool:
        """Check whether a record matching the given filters exists.

        Args:
            **kwargs: Column name/value pairs to filter by.

        Returns:
            True if a matching record exists, False otherwise.
        """
        stmt = select(func.count()).select_from(self.model)
        for column_name, value in kwargs.items():
            column = getattr(self.model, column_name, None)
            if column is not None:
                stmt = stmt.where(column == value)
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0
