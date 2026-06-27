# MyProject

A production-ready FastAPI project scaffold with async SQLAlchemy, Alembic migrations, structured logging, and comprehensive testing.

---

## Prerequisites

- **Python 3.14+**
- **Docker & Docker Compose** (for PostgreSQL and containerized deployment)
- **Make** (optional, for convenience targets)

---

## Local Setup

```bash
# 1. Clone the repository
git clone <repo-url> && cd my_project

# 2. Sync all dependencies and create virtual environment (runtime + dev + test)
uv sync

# 3. Copy the environment template and configure
cp .env.example .env
# Edit .env with your database credentials and secret key
```

---

## Database

### Start PostgreSQL with Docker Compose

```bash
docker compose up -d db
```

This starts a PostgreSQL 16 instance on port 5432 with default credentials (`myproject`/`myproject`).

### Run Migrations

```bash
make migrate
# or: alembic upgrade head
```

---

## Running Locally

```bash
make dev
# or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. When `DEBUG=true`, Swagger UI is at `/docs` and ReDoc at `/redoc`.

---

## Running with Docker

```bash
make docker-up
# or: docker compose up -d --build
```

This builds the app image and starts both PostgreSQL and the application. Migrations run automatically on container start.

```bash
make docker-down  # Stop all services
```

---

## Running Tests

Tests use **SQLite + aiosqlite** for speed and isolation — no PostgreSQL required.

```bash
make test
# or: pytest tests/ -v --cov=app --cov-report=term-missing
```

For an HTML coverage report:

```bash
make test-cov
```

---

## Linting & Type Checking

```bash
make lint       # ruff check + ruff format --check
make format     # ruff format (auto-fix)
make typecheck  # mypy strict mode
```

---

## Creating a Migration

```bash
make migration msg="add users table"
# or: alembic revision --autogenerate -m "add users table"
```

---

## Project Structure

```
my_project/
├── .github/workflows/   # CI/CD pipeline (GitHub Actions)
├── alembic/              # Database migrations (Alembic)
├── app/
│   ├── api/v1/routers/   # HTTP endpoint handlers (versioned)
│   ├── core/             # Cross-cutting: exceptions, logging, middleware, security
│   ├── models/           # SQLAlchemy ORM models
│   ├── repositories/     # Data access layer (repository pattern)
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic layer
│   ├── config.py         # Application settings (pydantic-settings)
│   ├── database.py       # Async engine, session factory, lifecycle
│   └── main.py           # App factory, lifespan, middleware, routing
├── tests/                # Async test suite (pytest + httpx)
├── docker-compose.yml    # PostgreSQL + app services
├── Dockerfile            # Multi-stage production build
├── Makefile              # Development convenience targets
└── pyproject.toml        # Dependencies, tool configuration
```

---

## Adding a New Resource

Follow these steps to add a new resource (e.g., `Post`):

1. **Model** — Create `app/models/post.py` with the SQLAlchemy model extending `Base` and `TimestampMixin`
2. **Repository** — Create `app/repositories/post.py` extending `BaseRepository[Post]`
3. **Schema** — Create `app/schemas/post.py` with `PostCreate`, `PostUpdate`, `PostRead`
4. **Service** — Create `app/services/post.py` with business logic over `PostRepository`
5. **Router** — Create `app/api/v1/routers/posts.py` with CRUD endpoints returning `APIResponse`
6. **Register Router** — Add `router.include_router(posts.router, ...)` in `app/api/v1/__init__.py`
7. **Migration** — Run `make migration msg="add posts table"` then `make migrate`
8. **Tests** — Add tests in `tests/test_posts.py`

---

## Environment Variables Reference

| Variable                      | Type        | Default     | Description                                      |
| ----------------------------- | ----------- | ----------- | ------------------------------------------------ |
| `PROJECT_NAME`                | `str`       | `MyProject` | Application display name                         |
| `DEBUG`                       | `bool`      | `false`     | Enable debug mode (Swagger UI, relaxed CORS/CSP) |
| `API_V1_PREFIX`               | `str`       | `/api/v1`   | URL prefix for v1 API routes                     |
| `ALLOWED_HOSTS`               | `list[str]` | `*`         | Allowed CORS origins (comma-separated)           |
| `DATABASE_URL`                | `str`       | —           | PostgreSQL connection URL (asyncpg driver)       |
| `DATABASE_POOL_SIZE`          | `int`       | `5`         | Connection pool size                             |
| `DATABASE_MAX_OVERFLOW`       | `int`       | `10`        | Maximum overflow connections                     |
| `DATABASE_ECHO`               | `bool`      | `false`     | Echo SQL statements to logs                      |
| `SECRET_KEY`                  | `str`       | —           | JWT signing key (min 32 chars)                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int`       | `60`        | JWT token expiration time in minutes             |
| `ALGORITHM`                   | `str`       | `HS256`     | JWT signing algorithm                            |
| `LOG_LEVEL`                   | `str`       | `INFO`      | Logging level (DEBUG, INFO, WARNING, ERROR)      |
| `LOG_FORMAT`                  | `str`       | `json`      | Log output format (`json` or `console`)          |

---

## License

MIT
