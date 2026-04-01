# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

doc-shape-shifter is a local-first document conversion toolkit. It routes each conversion through the best available backend engine via a conversion matrix with ordered fallback chains. Supports 10 formats (PDF, DOCX, Markdown, Plain Text, HTML, JSON, CSV, LaTeX, EPUB, RTF) across 7 backends (builtin, PyMuPDF, Pandoc, Docling, MarkItDown, Tabula, Mathpix).

## Commands

```bash
# Setup
uv pip install -e ".[dev]"

# Run CLI
uv run dss report.pdf report.md              # convert
uv run dss report.pdf --to docx              # convert with --to
uv run dss --list-backends                    # show backend status
uv run dss --list-formats                     # show supported conversion pairs
uv run dss -h                                 # help

# Tests
uv run pytest                                 # all tests
uv run pytest tests/unit/ -v                  # unit tests only
uv run pytest tests/integration/ -v           # integration tests only
uv run pytest -k test_json_to_csv             # single test by name

# Lint
uv run ruff check src/ tests/
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/
```

## Architecture

### Conversion Pipeline (detect -> route -> convert)

1. **Format detection** (`detector.py`): Three-layer detection — MIME type (python-magic), file extension, content heuristics. Returns `DocFormat` enum.

2. **Routing** (`router.py`): `CONVERSION_MATRIX` dict maps `(source_format, target_format)` -> ordered list of backend names. First available backend wins; others are fallbacks.

3. **Execution** (`converter.py`): `convert()` orchestrates the pipeline. Iterates the backend chain, tries each available backend, falls back on failure. Returns `ConversionResult` dataclass with success/failure, timing, and metadata.

### Backend System (`backends/`)

All backends inherit from `BaseBackend` ABC (`backends/base.py`) and implement:
- `is_available()` — check if dependencies are installed
- `convert(input_path, output_path, source_format, target_format)` -> `ConversionResult`
- `version_info()` — diagnostic string

Backend registry (`backends/__init__.py`) uses lazy singleton instantiation. Heavy libraries are imported inside backend methods to minimize startup cost.

| Backend | File | Scope |
|---------|------|-------|
| builtin | `builtin_backend.py` | stdlib-only: md<->txt, json<->csv, html->txt/csv |
| pymupdf | `pymupdf_backend.py` | PDF -> txt/md |
| pandoc | `pandoc_backend.py` | Universal bridge (30+ formats), CLI or pypandoc |
| docling | `docling_backend.py` | AI layout-aware: PDF/DOCX/HTML -> md/json/html/txt |
| markitdown | `markitdown_backend.py` | Multi-format -> md/txt/json |
| tabula | `tabula_backend.py` | PDF table extraction -> csv/json (requires Java) |
| mathpix | `mathpix_backend.py` | PDF/image -> LaTeX (commercial API) |

### Format System (`utils/formats.py`)

`DocFormat` enum with extension, MIME, and Pandoc format mappings. Note: `"plain"` is only a valid Pandoc *output* format — the pandoc backend handles this by omitting `-f` for plain text input.

## Testing

- **Unit tests** (`tests/unit/`): test_detector, test_router, test_converter, test_formats, test_backends — mock/synthetic inputs, no external deps needed
- **Integration tests** (`tests/integration/`): actual file conversions using fixture files in `tests/fixtures/`. Pandoc-dependent tests skip if pandoc isn't installed.
- **Test fixtures** (`tests/fixtures/`): sample files in md, txt, html, json, csv, tex, rtf

## Key Files

- `converter.py` — Main entry point for programmatic use: `from doc_shape_shifter.converter import convert`
- `router.py:CONVERSION_MATRIX` — The source of truth for what converts to what
- `backends/__init__.py:_register_backends()` — Where new backends get registered

## System Dependencies

Beyond Python packages: `pandoc` (for most non-builtin conversions), `java` (for tabula PDF table extraction). Optional: `python-magic`/`libmagic` (for MIME detection).

## Adding a New Backend

1. Create `src/doc_shape_shifter/backends/your_backend.py` subclassing `BaseBackend`
2. Register in `backends/__init__.py:_register_backends()`
3. Add conversion pairs to `router.py:CONVERSION_MATRIX`
4. Add dependency group in `pyproject.toml`
