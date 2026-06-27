"""User SQLAlchemy model.

Represents a user account in the system with email/username authentication
fields and role flags.
"""

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

__all__: list[str] = ["User"]


class User(TimestampMixin, Base):
    """User account model.

    Attributes:
        id: UUID primary key.
        email: Unique email address (max 254 chars).
        username: Unique username (max 50 chars).
        hashed_password: Bcrypt password hash (max 128 chars).
        is_active: Whether the user account is active.
        is_superuser: Whether the user has superuser privileges.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default="true",
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        default=False,
        server_default="false",
        nullable=False,
    )
