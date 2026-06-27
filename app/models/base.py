"""SQLAlchemy declarative base, naming conventions, and mixins.

Provides:
- `Base`: DeclarativeBase with constraint naming conventions for Alembic.
- `TimestampMixin`: Adds `created_at` and `updated_at` columns.
"""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__: list[str] = ["Base", "TimestampMixin", "NAMING_CONVENTION"]

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Uses a naming convention so Alembic autogenerate produces deterministic
    constraint names on PostgreSQL.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        pk = getattr(self, "id", "?")
        return f"{type(self).__name__}(id={pk})"


class TimestampMixin:
    """Mixin that adds `created_at` and `updated_at` timestamp columns.

    Both columns use server-side defaults and are timezone-aware.
    `updated_at` is automatically refreshed on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
