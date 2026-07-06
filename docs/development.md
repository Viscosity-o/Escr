# Development Guide

## Prerequisites

- Python 3.11+
- `pip` or a compatible package manager

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd global-intelligence-layer

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Set up environment variables
cp .env.example .env
# Edit .env and fill in required values
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=intelligence_layer --cov-report=term-missing

# Run a specific test file
pytest tests/collectors/test_base.py
```

## Linting and Type Checking

```bash
# Lint with ruff
ruff check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Type check with mypy
mypy src/
```

## Project Conventions

- All timestamps must be UTC and timezone-aware.
- All config access goes through `utils/config_loader.py`.
- All logging uses the logger from `utils/logging.py` via `get_logger(__name__)`.
- Secrets are always read from environment variables — never hardcoded or in YAML.
- New data sources are added as new sub-packages under `collectors/`, with matching
  modules in `validators/`, `normalizers/`, `tests/`, and an entry in `config/sources.yaml`.

See [adding_a_new_source.md](adding_a_new_source.md) for a step-by-step walkthrough.
