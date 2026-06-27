"""Structured logging configuration using structlog.

Provides:
- `configure_logging(settings)`: call once at startup to set up processors
- `get_logger(name)`: returns a bound structlog logger
- `request_id_ctx_var`: ContextVar for per-request ID propagation
"""

import contextvars
import logging
import sys

import structlog
from structlog.types import EventDict, Processor

from app.config import Settings

__all__: list[str] = ["configure_logging", "get_logger", "request_id_ctx_var"]

# ── Context variable for request-id propagation ─────────────────────────────

request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="",
)


# ── Custom processors ───────────────────────────────────────────────────────


def _add_request_id(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """Inject the current request_id into every log entry."""
    request_id = request_id_ctx_var.get("")
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def _drop_color_message(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """Remove uvicorn's color_message key to avoid duplicate output."""
    event_dict.pop("color_message", None)
    return event_dict


# ── Configuration ────────────────────────────────────────────────────────────


def configure_logging(settings: Settings) -> None:
    """Configure structlog and stdlib logging based on application settings."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Shared processors for both structlog and stdlib integration
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _add_request_id,
        _drop_color_message,
        structlog.processors.UnicodeDecoder(),
    ]

    # Choose renderer based on settings
    if settings.LOG_FORMAT == "console":
        renderer: Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging with structlog's ProcessorFormatter
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Apply to root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress noisy loggers
    for noisy_logger in ("uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger for the given module name."""
    return structlog.get_logger(name)  # type: ignore[return-value]
