# Doc-Shape-Shifter

[![CI](https://github.com/jon-chun/doc-shape-shifter/actions/workflows/ci.yml/badge.svg)](https://github.com/jon-chun/doc-shape-shifter/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent document format converter that automatically selects the best conversion backend for any source-to-target format pair. Built for AI researchers and developers who need reliable, high-fidelity document conversion for RAG pipelines, data processing, and academic workflows.

---

## Table of Contents

1. [Why Doc-Shape-Shifter?](#why-doc-shape-shifter)
2. [Supported Formats](#supported-formats)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [Interpreting Output](#interpreting-output)
9. [Project Structure](#project-structure)
10. [Development](#development)
11. [Roadmap](#roadmap)
12. [License](#license)

---

## Why Doc-Shape-Shifter?

The document conversion landscape is fragmented across dozens of tools (Pandoc, Docling, PyMuPDF, MarkItDown, Mathpix, Tabula, etc.), each excelling at different format pairs. Choosing the right tool for a given conversion requires deep domain knowledge. Doc-Shape-Shifter solves this by:

- Providing a **single CLI command** (`dss`) and Python API for all conversions.
- Maintaining a **conversion matrix** that maps every (source, target) pair to a ranked list of backends, derived from the March 2026 Neural Document Parsing survey benchmarks.
- **Automatically falling back** to the next-best backend if the primary one fails or is not installed.
- Being **modular**: install only the backends you need, or install everything with `pip install -e ".[all]"`.

---

## Supported Formats

### Tier 1 (MVP - Current)

| Format | Extensions | Read | Write |
|---|---|---|---|
| PDF (native text) | `.pdf` | Yes | Yes |
| Microsoft Word | `.docx` | Yes | Yes |
| Markdown | `.md`, `.markdown` | Yes | Yes |
| Plain Text | `.txt`, `.text` | Yes | Yes |
| HTML | `.html`, `.htm` | Yes | Yes |
| JSON | `.json` | Yes | Yes |
| CSV | `.csv` | Yes | Yes |
| LaTeX | `.tex`, `.latex` | Yes | Yes |
| EPUB | `.epub` | Yes | Yes |
| RTF | `.rtf` | Yes | Yes |

### Future Tiers

- **Tier 2**: PPTX, XLSX, XML, ODT
- **Tier 3**: Scanned PDF (OCR), PNG/JPG (OCR), SVG, audio transcription
- **Specialized pipelines**: Optical Music Recognition (OMR), Optical Table Recognition (OTR), image enhancement/restoration/upscaling

---

## Architecture

Doc-Shape-Shifter uses a **Router-Worker** pattern with automatic fallback:

```
Input File
    |
    v
[Format Detector] ---- MIME type (python-magic)
    |                   File extension
    |                   Content heuristics
    v
[Route Selector] ----- Conversion matrix lookup
    |                   Returns ranked backend list
    v
[Backend Worker] ----- Try backend #1
    |                   On failure -> try backend #2
    |                   On failure -> try backend #3 ...
    v
Output File + ConversionResult metadata
```

### Backend Priority Matrix (Selected Pairs)

| Conversion | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| PDF -> Markdown | Docling | PyMuPDF | Pandoc |
| PDF -> Plain Text | PyMuPDF | Docling | Pandoc |
| PDF -> CSV | Tabula | - | - |
| PDF -> LaTeX | Mathpix | Pandoc | - |
| DOCX -> Markdown | MarkItDown | Docling | Pandoc |
| HTML -> Markdown | Docling | Pandoc | - |
| JSON -> CSV | builtin | - | - |
| Markdown -> DOCX | Pandoc | - | - |

Run `dss --list-formats` to see the complete matrix with all 60+ defined conversion pairs.

---

## Prerequisites

### Required

| Dependency | Install Command | Purpose |
|---|---|---|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) | Runtime |
| **Pandoc >= 3.1** | `brew install pandoc` | Universal format bridge |
| **libmagic** | `brew install libmagic` | MIME type detection |

### Optional

| Dependency | Install Command | Purpose |
|---|---|---|
| **Java Runtime** | `brew install openjdk` | Required for Tabula (PDF table extraction) |
| **Mathpix API key** | [mathpix.com](https://mathpix.com) | PDF -> LaTeX with math notation |

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/jon-chun/doc-shape-shifter.git
cd doc-shape-shifter
```

### Step 2: Create a Virtual Environment

```bash
# Using uv (recommended, fastest)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.11 .venv
source .venv/bin/activate

# OR using standard venv
python3.11 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install System Dependencies

```bash
brew install pandoc libmagic
```

### Step 4: Install the Package

```bash
# Core only (PyMuPDF + python-magic + Click + Rich)
pip install -e .

# Core + Pandoc bridge
pip install -e ".[pandoc]"

# Everything (all backends)
pip install -e ".[all]"

# Development tools (linting, testing, type checking)
pip install -e ".[dev]"
```

### Step 5: Verify Installation

```bash
# Quick backend check
python scripts/check_backends.py

# Or via CLI
dss --list-backends
```

---

## Configuration

### Environment Variables (Optional)

Copy the example and edit:

```bash
cp .env.example .env
```

| Variable | Required | Purpose |
|---|---|---|
| `MATHPIX_APP_ID` | Only for PDF->LaTeX | Mathpix API application ID |
| `MATHPIX_APP_KEY` | Only for PDF->LaTeX | Mathpix API secret key |

If these are not set, the Mathpix backend is automatically skipped and Pandoc is used as fallback for LaTeX conversion.

### Logging

Logs are written to `logs/dss_YYYYMMDD.jsonl` in structured JSON-lines format. Control verbosity via the CLI:

| Flag | Level | Shows |
|---|---|---|
| (none) | WARNING | Errors and warnings only |
| `-v` | INFO | Conversion progress, backend selection |
| `-vv` | DEBUG | MIME detection, backend availability, full traces |

---

## Usage

### CLI

```bash
# Convert PDF to Markdown (auto-selects best backend)
dss report.pdf report.md

# Specify target format (output filename auto-generated)
dss paper.tex --to docx
# -> produces paper.docx

# Force a specific backend
dss document.docx --to md --backend pandoc

# Extract tables from PDF to CSV
dss financial-report.pdf --to csv

# Verbose output for debugging
dss input.html --to json -vv

# Disable fallback (fail if primary backend fails)
dss input.pdf output.md --no-fallback

# Diagnostics
dss --list-backends       # Show installed backends and versions
dss --list-formats        # Show all supported conversion pairs
dss --version             # Show package version
dss --help                # Full help text
```

### Python API

```python
from doc_shape_shifter.converter import convert

# Simple conversion
result = convert("report.pdf", "report.md")

if result.success:
    print(f"Converted via {result.backend_name} in {result.duration_seconds:.2f}s")
    print(f"Output: {result.output_path} ({result.file_size_bytes} bytes)")
else:
    print(f"Failed: {result.error_message}")

# With explicit options
result = convert(
    input_path="paper.tex",
    output_path="output/paper.docx",
    target_format="docx",     # Can also be inferred from output extension
    backend="pandoc",          # Force specific backend (optional)
    fallback=True,             # Try alternates on failure (default: True)
)

# Check warnings (e.g., "scanned PDF, no text extracted")
for warning in result.warnings:
    print(f"Warning: {warning}")
```

### Format Detection (Standalone)

```python
from doc_shape_shifter.detector import detect_format

fmt = detect_format("mystery_file.dat")
print(fmt)  # e.g., DocFormat.PDF
```

### Backend Inspection

```python
from doc_shape_shifter.backends import list_backends

for name, available in list_backends():
    print(f"{name}: {'installed' if available else 'missing'}")
```

---

## Interpreting Output

### ConversionResult Object

Every conversion returns a `ConversionResult` dataclass:

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | Whether the conversion completed |
| `output_path` | `Path or None` | Path to the output file (None if failed) |
| `backend_name` | `str` | Which backend performed the conversion |
| `duration_seconds` | `float` | Wall-clock time for the full operation |
| `source_format` | `str` | Detected source format |
| `target_format` | `str` | Requested target format |
| `file_size_bytes` | `int or None` | Size of the output file |
| `error_message` | `str or None` | Error details if failed |
| `warnings` | `list[str]` | Non-fatal warnings (e.g., empty text from scanned PDF) |

### CLI Exit Codes

| Code | Meaning |
|---|---|
| `0` | Conversion succeeded |
| `1` | Conversion failed (all backends exhausted or invalid arguments) |

### Log File Format

Each line in `logs/dss_YYYYMMDD.jsonl` is a JSON object:

```json
{
  "timestamp": "2026-03-31T14:22:05.123456+00:00",
  "level": "INFO",
  "logger": "doc_shape_shifter.converter",
  "message": "Conversion SUCCESS via docling in 2.34s",
  "source_format": "pdf",
  "target_format": "md",
  "backend": "docling",
  "duration_s": 2.34,
  "file_size_bytes": 15234
}
```

---

## Project Structure

```
doc-shape-shifter/
├── .github/workflows/ci.yml     # GitHub Actions CI (lint + test matrix)
├── .env.example                  # Template for optional API keys
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE                       # MIT
├── README.md                     # This file
├── pyproject.toml                # PEP 621 metadata, Hatch build, tool config
│
├── src/doc_shape_shifter/        # Main package (PyPI-ready src layout)
│   ├── __init__.py               # Package version
│   ├── cli.py                    # Click CLI entry point (`dss`)
│   ├── converter.py              # Orchestration: detect -> route -> convert
│   ├── detector.py               # MIME / extension / heuristic format detection
│   ├── router.py                 # Conversion matrix and backend selection
│   ├── backends/                 # Pluggable conversion backends
│   │   ├── __init__.py           # Backend registry
│   │   ├── base.py               # Abstract base class + ConversionResult
│   │   ├── builtin_backend.py    # Python stdlib (always available)
│   │   ├── pymupdf_backend.py    # Fast PDF text extraction
│   │   ├── pandoc_backend.py     # Universal format bridge
│   │   ├── docling_backend.py    # AI-powered layout parsing (IBM)
│   │   ├── markitdown_backend.py # Multi-format -> Markdown (Microsoft)
│   │   ├── tabula_backend.py     # PDF table -> CSV/JSON
│   │   └── mathpix_backend.py    # Math PDF -> LaTeX (API)
│   ├── utils/
│   │   ├── formats.py            # DocFormat enum, extension/MIME maps
│   │   └── logging_config.py     # Structured JSON logging
│   └── pipelines/                # Future expansion (not yet active)
│       ├── ocr/                  # Scanned PDF / image OCR
│       ├── otr/                  # Optical Table Recognition
│       ├── omr/                  # Optical Music Recognition
│       └── image/                # Enhancement, restoration, upscaling
│
├── tests/
│   ├── unit/                     # Fast isolated tests
│   │   ├── test_detector.py
│   │   ├── test_router.py
│   │   └── test_converter.py
│   ├── integration/              # End-to-end tests (future)
│   └── fixtures/                 # Sample files for testing
│
├── docs/
│   ├── prd.md                    # Product Requirements Document
│   ├── tech-spec.md              # Technical Specification
│   ├── user-manual.md            # Comprehensive user guide
│   ├── images/                   # Documentation images
│   └── examples/                 # Example scripts and workflows
│
├── scripts/
│   └── check_backends.py         # Diagnostic: verify backend installation
│
├── logs/                         # Runtime logs (gitignored except .gitkeep)
└── output/                       # Default output directory (gitignored)
```

---

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest                           # All tests
pytest tests/unit/ -v            # Unit tests only
pytest --cov=doc_shape_shifter   # With coverage
```

### Linting and Formatting

```bash
ruff check src/ tests/           # Lint
ruff format src/ tests/          # Auto-format
mypy src/                        # Type checking
```

### Adding a New Backend

1. Create `src/doc_shape_shifter/backends/your_backend.py`, subclass `BaseBackend`
2. Implement `name`, `is_available()`, `convert()`, `version_info()`
3. Register in `backends/__init__.py` -> `_register_backends()`
4. Add `(source, target) -> ["your_backend", ...]` entries in `router.py`
5. Add optional dependency group in `pyproject.toml`
6. Write tests in `tests/unit/test_your_backend.py`
7. Update CHANGELOG.md

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

---

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| **v0.1 (MVP)** | Tier 1 formats, CLI, 7 backends, fallback chains | **Current** |
| **v0.2** | Confidence scoring, batch mode, progress bars | Planned |
| **v0.3** | Tier 2 formats (PPTX, XLSX, XML, ODT) | Planned |
| **v0.4** | OCR pipeline (MinerU, Marker, Surya) | Planned |
| **v0.5** | Image pipeline (enhancement, upscaling) | Planned |
| **v0.6** | OMR pipeline (MusicXML, MIDI) | Planned |
| **v1.0** | FastAPI server, Docker image, quality scoring loop | Planned |

---

## License

[MIT](LICENSE) - Jon Chun, 2026
