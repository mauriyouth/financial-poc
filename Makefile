.PHONY: help api worker front local-stack local-dev stack-down stack-clean
.PHONY: test test-back test-front lint lint-back lint-front fix fix-back e2e-tests
.PHONY: format format-back precommit install-hooks

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Services:"
	@echo "  make api          - Run backend API server"
	@echo "  make worker       - Run document parsing worker"
	@echo "  make front        - Run frontend dev server"
	@echo "  make local-stack  - Start all infrastructure (Redis, DB, MinIO, etc.)"
	@echo "  make local-dev    - Start infrastructure + API"
	@echo "  make stack-down   - Stop all infrastructure"
	@echo "  make stack-clean  - Stop infrastructure and remove volumes"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests (backend + frontend)"
	@echo "  make test-back    - Run backend tests"
	@echo "  make test-front   - Run frontend tests"
	@echo ""
	@echo "Linting & Formatting:"
	@echo "  make lint         - Lint all code (backend + frontend)"
	@echo "  make lint-back    - Lint backend"
	@echo "  make lint-front   - Lint frontend"
	@echo "  make fix          - Auto-fix linting issues (backend)"
	@echo "  make format       - Format backend code"
	@echo ""
	@echo "Pre-commit:"
	@echo "  make precommit    - Run all quality checks"
	@echo "  make install-hooks - Install git pre-commit hooks"
	@echo ""
	@echo "CI/CD & Integration:"
	@echo "  make e2e-tests    - Build images and run full system integration tests"

# === SERVICES ===

api:
	cd backend && uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd backend && uv run python worker.py

front:
	cd frontend && npm run dev

storybook:
	cd frontend && npm run storybook

dev-ui:
	$(MAKE) -j 2 front storybook

local-stack:
	cd infra/local-stack && docker-compose up -d

local-dev:
	cd infra/local-stack && docker-compose up -d
	$(MAKE) api

stack-down:
	cd infra/local-stack && docker-compose down

stack-clean:
	cd infra/local-stack && docker-compose down -v

# === TESTING ===

test: test-back test-front

test-back:
	cd backend && uv run pytest -v

test-back-cov:
	cd backend && uv run pytest -v --cov=src --cov-report=term-missing --cov-report=html

test-front:
	cd frontend && npm test

# === LINTING & FORMATTING ===

lint: lint-back lint-front

lint-back:
	cd backend && uv run ruff check .

lint-front:
	cd frontend && npm run lint

fix:
	cd backend && uv run ruff check --fix .

format:
	cd backend && uv run ruff format .

format-check:
	cd backend && uv run ruff format --check .

# === PRE-COMMIT ===

precommit: lint format-check test
	@echo "✓ All quality checks passed!"

install-hooks:
	cd backend && uv run pre-commit install
	@echo "✓ Pre-commit hooks installed!"

# === E2E TESTING ===

e2e-tests:
	@echo "🐳 Building images for E2E testing..."
	docker-compose -f docker-compose.e2e.yml build
	@echo "🚀 Starting E2E environment..."
	docker-compose -f docker-compose.e2e.yml up -d
	@echo "⏳ Waiting for services to be healthy..."
	# Give it some time to settle
	sleep 15
	@echo "🧪 Running integration tests..."
	# Install test dependencies locally if needed, or run from a container
	cd backend && uv run pytest ../tests/e2e/test_connection.py
	@echo "🧹 Cleaning up..."
	docker-compose -f docker-compose.e2e.yml down -v
	@echo "✅ E2E tests completed successfully!"
