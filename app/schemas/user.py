"""User Pydantic schemas for request/response validation.

Provides:
- `UserBase`: shared email + username fields with validators.
- `UserCreate`: creation schema with password validation.
- `UserUpdate`: partial update schema (all fields optional).
- `UserRead`: response schema with database-generated fields.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

__all__: list[str] = ["UserBase", "UserCreate", "UserUpdate", "UserRead"]


class UserBase(BaseModel):
    """Base user schema with shared validation rules.

    Attributes:
        email: Valid email address.
        username: 3–50 characters, alphanumeric + underscore only.
    """

    email: EmailStr
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username: 3–50 chars, alphanumeric + underscore."""
        if len(v) < 3 or len(v) > 50:
            msg = "Username must be between 3 and 50 characters"
            raise ValueError(msg)
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            msg = "Username must contain only alphanumeric characters and underscores"
            raise ValueError(msg)
        return v


class UserCreate(UserBase):
    """Schema for creating a new user.

    Attributes:
        password: Must be at least 8 characters with at least one digit.
    """

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password: ≥8 chars with at least one digit."""
        if len(v) < 8:
            msg = "Password must be at least 8 characters long"
            raise ValueError(msg)
        if not any(char.isdigit() for char in v):
            msg = "Password must contain at least one digit"
            raise ValueError(msg)
        return v


class UserUpdate(BaseModel):
    """Schema for partially updating a user.

    All fields are optional — only provided fields are updated.
    """

    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Validate username if provided: 3–50 chars, alphanumeric + underscore."""
        if v is not None:
            if len(v) < 3 or len(v) > 50:
                msg = "Username must be between 3 and 50 characters"
                raise ValueError(msg)
            if not re.match(r"^[a-zA-Z0-9_]+$", v):
                msg = "Username must contain only alphanumeric characters and underscores"
                raise ValueError(msg)
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Validate password if provided: ≥8 chars with at least one digit."""
        if v is not None:
            if len(v) < 8:
                msg = "Password must be at least 8 characters long"
                raise ValueError(msg)
            if not any(char.isdigit() for char in v):
                msg = "Password must contain at least one digit"
                raise ValueError(msg)
        return v


class UserRead(UserBase):
    """Schema for reading/returning a user in API responses.

    Includes database-generated fields like id, timestamps, and flags.
    """

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
