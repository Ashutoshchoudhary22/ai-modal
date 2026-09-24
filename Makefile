.PHONY: help install test lint format dev-ai-api docker-up docker-down db-migrate db-status clean

help:
	@echo "AI Platform — Development Commands"
	@echo ""
	@echo "  make install     Install Python and Node dependencies"
	@echo "  make test        Run all tests"
	@echo "  make lint        Run linters"
	@echo "  make format      Format code"
	@echo "  make dev-ai-api  Start AI API in development mode"
	@echo "  make docker-up   Start MySQL and Redis"
	@echo "  make docker-down Stop Docker services"
	@echo "  make db-migrate  Bootstrap (if empty) and apply SQL migrations"
	@echo "  make db-status   Show migration status"

install:
	pip install -e "packages/protocol[dev]" -e "packages/shared[dev]" -e "services/ai-api[dev]" -e "training[train,dev]"
	npm install

test:
	pytest
	npm test

lint:
	ruff check packages services tests training
	ruff format --check packages services tests training
	npm run lint

format:
	ruff format packages services tests training
	ruff check --fix packages services tests training
	npm run format

dev-ai-api:
	cd services/ai-api && uvicorn ai_api.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	npm run dev --workspace @ai-platform/web

docker-up:
	docker compose up -d mysql redis

docker-down:
	docker compose down

db-migrate:
	python scripts/db_migrate.py --bootstrap

db-status:
	python scripts/db_migrate.py --status

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
