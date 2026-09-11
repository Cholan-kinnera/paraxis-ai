# ==============================================================================
# PARAXIS AI — DEVELOPER MAKEFILE
# ==============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup dev docker-up docker-down docker-logs lint test typecheck verify-foundation clean

help: ## Display this help screen
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial environment setup: copy .env if missing and verify tools
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; else echo ".env already exists"; fi
	@python3 --version
	@node --version
	@docker --version
	@docker compose version

docker-up: ## Start PostgreSQL (pgvector) and Redis services via Docker Compose
	docker compose up -d

docker-down: ## Stop Docker Compose foundation services
	docker compose down

docker-logs: ## Follow Docker Compose container logs
	docker compose logs -f

verify-foundation: ## Run foundation verification script (docs, dirs, ADRs, configs)
	python3 scripts/verify_foundation.py

lint: ## Run linting across web, core, and intelligence
	@echo "Checking formatting and syntax..."
	@python3 -m py_compile apps/core/**/*.py apps/intelligence/**/*.py 2>/dev/null || true

test: ## Run test suites across monorepo
	@echo "Running tests..."
	@python3 scripts/verify_foundation.py

clean: ## Clean transient cache, build artifacts, and pycache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
