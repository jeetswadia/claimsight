.PHONY: help install verify lint format test test-cov db-init data-download data-load clean

help:
	@echo "ClaimSight — common commands"
	@echo ""
	@echo "  make install        Install package + dev dependencies"
	@echo "  make verify         Verify all services are reachable (.env keys, DB, APIs)"
	@echo "  make lint           Run ruff + mypy"
	@echo "  make format         Run black + ruff format"
	@echo "  make test           Run pytest"
	@echo "  make test-cov       Run pytest with coverage report"
	@echo "  make db-init        Apply database schema"
	@echo "  make data-download  Download SynPUF synthetic claims data"
	@echo "  make data-load      Load SynPUF data into Postgres"
	@echo "  make clean          Remove caches and build artifacts"

install:
	pip install -e ".[dev,eval]"
	pre-commit install

verify:
	python scripts/00_verify_env.py

lint:
	ruff check src/ tests/ scripts/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/ scripts/
	ruff check --fix src/ tests/ scripts/

test:
	pytest -v

test-cov:
	pytest --cov=src --cov-report=term-missing --cov-report=html

db-init:
	@if [ -z "$$DATABASE_URL" ]; then echo "ERROR: DATABASE_URL not set"; exit 1; fi
	psql "$$DATABASE_URL" -f scripts/02_apply_schema.sql

data-download:
	python scripts/01_download_synpuf.py

data-load:
	python scripts/03_load_synpuf.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
