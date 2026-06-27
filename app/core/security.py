"""Security utilities — password hashing and JWT token stubs.

Uses passlib with bcrypt for password hashing.
JWT functions use python-jose for token creation and verification.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

__all__: list[str] = [
    "pwd_context",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)  # type: ignore[no-any-return]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload to encode in the token.
        expires_delta: Optional custom expiration time. Defaults to
            `ACCESS_TOKEN_EXPIRE_MINUTES` from settings.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta is not None:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT access token.

    Args:
        token: The encoded JWT string.

    Returns:
        The decoded payload dictionary, or None if the token is invalid.
    """
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
