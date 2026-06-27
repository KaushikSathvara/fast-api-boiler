"""HTTP middleware for request logging and security headers.

`RequestLoggingMiddleware`: generates a unique request_id, logs request
duration and status, and injects `X-Request-ID` into responses.

`SecurityHeadersMiddleware`: adds security-related response headers and
removes the `Server` header.
"""

import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_ctx_var

__all__: list[str] = ["RequestLoggingMiddleware", "SecurityHeadersMiddleware"]

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status_code, and duration_ms.

    Generates a unique `request_id` per request, stores it in the context var
    for downstream consumers, and attaches it as an `X-Request-ID` response
    header.

    Never logs request bodies.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and log its completion."""
        request_id = uuid4().hex
        request_id_ctx_var.set(request_id)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security response headers and remove the Server header.

    Headers are relaxed when DEBUG=True (Content-Security-Policy allows
    unsafe-inline for development tools like Swagger UI).
    """

    def __init__(self, app: object, debug: bool = False) -> None:  # noqa: FBT001, FBT002
        super().__init__(app)  # type: ignore[arg-type]
        self.debug = debug

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and add security headers to the response."""
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if self.debug:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Remove the Server header to avoid leaking server information
        if "Server" in response.headers:
            del response.headers["Server"]

        return response
