# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies using uv.lock
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.14-slim AS runtime

WORKDIR /app

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Expose the application port
EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
