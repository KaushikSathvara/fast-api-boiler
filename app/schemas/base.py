"""Base response schemas — API envelope, pagination, and page params.

All routers must return `APIResponse[T]` or `APIResponse[PaginatedResponse[T]]`.
Never return raw schema instances.
"""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

__all__: list[str] = ["APIResponse", "PaginatedResponse", "PageParams"]

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for all API responses.

    Attributes:
        success: Whether the request was successful.
        data: The response payload (generic type T).
        message: Optional human-readable message.
        errors: Optional list of error details.
        request_id: The unique request identifier (injected by middleware).
    """

    success: bool = True
    data: T | None = None
    message: str | None = None
    errors: list[dict[str, str]] | None = None
    request_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper.

    Attributes:
        items: The list of items for the current page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        pages: Total number of pages.
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[T]:
        """Create a PaginatedResponse computing the total pages."""
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class PageParams(BaseModel):
    """Query parameters for pagination.

    Attributes:
        page: Page number (1-indexed, minimum 1).
        page_size: Number of items per page (1–100).
    """

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET from page and page_size."""
        return (self.page - 1) * self.page_size
