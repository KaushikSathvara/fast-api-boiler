.DEFAULT_GOAL := help

.PHONY: install lint format typecheck test test-cov migrate migration dev docker-up docker-down clean help

install: ## Install all deps including dev and test
	uv sync

lint: ## Run ruff check + ruff format --check
	ruff check app/ tests/
	ruff format --check app/ tests/

format: ## Run ruff format
	ruff format app/ tests/

typecheck: ## Run mypy in strict mode
	uv run mypy app/

test: ## Run pytest with coverage
	uv run pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

test-cov: ## Run pytest, generate and open HTML coverage report
	uv run pytest tests/ -v --cov=app --cov-report=html
	@echo "Coverage report generated at htmlcov/index.html"
	open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || true

migrate: ## Run alembic upgrade head
	uv run alembic upgrade head

migration: ## Create new migration: make migration msg="add users table"
	uv run alembic revision --autogenerate -m "$(msg)"

dev: ## Run uvicorn in reload mode
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up: ## Start docker-compose services
	docker compose up -d --build

docker-down: ## Stop docker-compose services
	docker compose down

clean: ## Remove __pycache__, .mypy_cache, .pytest_cache, .ruff_cache, test.db
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage test.db

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
