# Merge Audit Log — 2026-03-31

## Summary

Merged `repo-shape-shifter_opus46-cowork/` (cowork MVP) into root repo, replacing the original
root architecture. The cowork version was chosen as the primary because it provides:

- A proper backend abstraction (BaseBackend ABC + 7 concrete backends)
- An explicit conversion matrix (60+ format pairs with fallback chains)
- Multi-layer format detection (MIME + extension + heuristics)
- Structured JSON logging
- Click-based CLI (vs argparse)
- 28+ unit tests (vs 4 in root)
- MarkItDown backend (not present in root)
- RTF format support (not present in root)
- Rich console output
- GitHub Actions CI/CD pipeline

## Architecture Changes

### Root (original) -> Cowork (merged)

| Component | Root | Cowork (merged) |
|-----------|------|-----------------|
| CLI framework | argparse | Click |
| CLI commands | doctor, plan, convert | convert, --list-backends, --list-formats |
| Entry point | `doc-shape-shifter` / `dss` | `dss` |
| Routing | ConversionRouter class (score-based) | CONVERSION_MATRIX dict (chain-based) |
| Engine abstraction | adapter functions in adapters.py | BaseBackend ABC + backend classes |
| Intermediate repr | DocumentIR dataclass | Backend-internal (no shared IR) |
| Format enum | DocumentFormat (11 formats) | DocFormat (10 formats, adds RTF, drops PPTX/XLSX) |
| Format detection | Extension only | MIME + Extension + Heuristic |
| Logging | None (stdout) | Structured JSON (file + console) |
| Tests | 4 router tests | 28+ (detector, router, converter, formats, backends) |
| Backends | 5 (native, pandoc, pymupdf, docling, tabula) | 7 (+markitdown, +mathpix full impl) |

### Files Replaced (archived to archive/root_original_src/)

- `src/doc_shape_shifter/__init__.py`
- `src/doc_shape_shifter/__main__.py`
- `src/doc_shape_shifter/cli.py`
- `src/doc_shape_shifter/core/__init__.py`
- `src/doc_shape_shifter/core/types.py`
- `src/doc_shape_shifter/core/router.py`
- `src/doc_shape_shifter/core/runtime.py`
- `src/doc_shape_shifter/engines/__init__.py`
- `src/doc_shape_shifter/engines/adapters.py`
- `src/doc_shape_shifter/ocr/__init__.py`
- `src/doc_shape_shifter/otr/__init__.py`
- `src/doc_shape_shifter/omr/__init__.py`
- `src/doc_shape_shifter/restoration/__init__.py`
- `src/doc_shape_shifter/pipelines/__init__.py`

### Files Replaced (archived to archive/root_original_tests/)

- `tests/test_router.py`

### Files Replaced (archived to archive/)

- `pyproject.toml` -> `archive/root_original_pyproject.toml`
- `.gitignore` -> `archive/root_original_gitignore`

### New Files Added (from cowork)

- `src/doc_shape_shifter/converter.py` — Orchestration module
- `src/doc_shape_shifter/detector.py` — MIME + extension + heuristic detection
- `src/doc_shape_shifter/router.py` — Conversion matrix
- `src/doc_shape_shifter/backends/__init__.py` — Backend registry
- `src/doc_shape_shifter/backends/base.py` — BaseBackend ABC
- `src/doc_shape_shifter/backends/builtin_backend.py` — stdlib conversions
- `src/doc_shape_shifter/backends/pymupdf_backend.py` — PDF extraction
- `src/doc_shape_shifter/backends/pandoc_backend.py` — Universal bridge
- `src/doc_shape_shifter/backends/docling_backend.py` — AI layout parser
- `src/doc_shape_shifter/backends/markitdown_backend.py` — MS multi-format -> MD
- `src/doc_shape_shifter/backends/tabula_backend.py` — PDF table extraction
- `src/doc_shape_shifter/backends/mathpix_backend.py` — Math OCR API
- `src/doc_shape_shifter/utils/__init__.py`
- `src/doc_shape_shifter/utils/formats.py` — DocFormat enum + maps
- `src/doc_shape_shifter/utils/logging_config.py` — JSON logging
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/unit/test_detector.py`
- `tests/unit/test_router.py`
- `tests/unit/test_converter.py`
- `tests/unit/test_formats.py`
- `tests/unit/test_backends.py`
- `scripts/check_backends.py`
- `.github/workflows/ci.yml`
- `LICENSE`
- `CHANGELOG.md`
- `CONTRIBUTING.md`

### Files Kept From Root (not in cowork)

- `docs/prd.md` — Product requirements
- `docs/tech-spec.md` — Technical specification
- `docs/user-manual.md` — User manual
- `docs/research/` — Research artifacts
- `scripts/sync_repo.sh` — Git sync helper
- `scripts/build_release_zip.sh` — Release archive builder
- `scripts/bootstrap_mac_m4.sh` — Apple Silicon bootstrap
- `README.md` — Kept as-is (will need update to reflect new CLI)
- `uv.lock` — Kept (will be regenerated on next `uv sync`)

### Directories Removed (replaced by cowork equivalents)

- `src/doc_shape_shifter/core/` — Replaced by backends/, utils/, converter.py, detector.py, router.py
- `src/doc_shape_shifter/engines/` — Replaced by backends/
- `src/doc_shape_shifter/ocr/` — Replaced by pipelines/ocr/
- `src/doc_shape_shifter/otr/` — Replaced by pipelines/otr/
- `src/doc_shape_shifter/omr/` — Replaced by pipelines/omr/
- `src/doc_shape_shifter/restoration/` — Replaced by pipelines/image/

### New Directories Created

- `logs/` — Runtime JSON logs
- `output/` — Default conversion output
- `archive/` — Archived pre-merge files
- `.github/workflows/` — CI/CD

### Dependency Changes

| Root pyproject.toml | Cowork pyproject.toml |
|--------------------|-----------------------|
| requires-python >=3.12 | requires-python >=3.10 |
| docling, pymupdf4llm, requests, tabula-py | click, python-magic, pymupdf, rich |
| dev: pytest, ruff | dev: pytest, pytest-cov, ruff, mypy |
| entry: doc-shape-shifter, dss | entry: dss |
| No optional groups | pandoc, docling, markitdown, tabula, mathpix, ocr, image, all |

### New Tests Added Beyond Cowork

- `tests/unit/test_formats.py` — Format utility tests (roundtrip, mapping consistency)
- `tests/unit/test_backends.py` — Backend registry and ConversionResult tests
- Additional converter tests: txt_to_md, json_to_txt, csv_to_txt
