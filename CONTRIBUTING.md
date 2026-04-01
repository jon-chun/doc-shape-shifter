# Contributing to Doc-Shape-Shifter

Thank you for your interest in contributing.

## Development Setup

```bash
git clone https://github.com/jon-chun/doc-shape-shifter.git
cd doc-shape-shifter
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,all]"
brew install pandoc libmagic
```

## Running Tests

```bash
pytest tests/ -v --tb=short
```

## Code Style

This project uses **Ruff** for linting and formatting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Adding a New Backend

1. Create `src/doc_shape_shifter/backends/your_backend.py` subclassing `BaseBackend`
2. Implement `is_available()`, `convert()`, and `version_info()`
3. Register the class in `backends/__init__.py` `_register_backends()`
4. Add conversion pairs to `router.py` `CONVERSION_MATRIX`
5. Add a dependency group in `pyproject.toml` `[project.optional-dependencies]`
6. Write unit tests in `tests/unit/test_your_backend.py`

## Pull Request Process

1. Fork the repository and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass and linting is clean
4. Update CHANGELOG.md
5. Submit a PR with a clear description
