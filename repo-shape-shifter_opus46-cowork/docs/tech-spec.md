# Technical Specification: Doc-Shape-Shifter MVP (v0.1)

**Date**: 2026-03-31
**Scope**: Tier 1 format conversions — PDF, DOCX, Markdown, Plain Text, HTML, JSON, CSV, LaTeX, EPUB, RTF

---

## 1. Project Structure

```
doc-shape-shifter/
├── pyproject.toml              # Project metadata, dependencies, entry points
├── README.md                   # Setup and usage instructions
├── .gitignore
├── .env.example                # Template for optional API keys (Mathpix)
├── src/
│   └── doc_shape_shifter/
│       ├── __init__.py         # Package init, version
│       ├── cli.py              # Click-based CLI entry point
│       ├── converter.py        # Main orchestration: detect → route → convert
│       ├── detector.py         # MIME type / format detection
│       ├── router.py           # Conversion matrix + backend selection
│       ├── backends/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract base class for backends
│       │   ├── pandoc_backend.py
│       │   ├── docling_backend.py
│       │   ├── pymupdf_backend.py
│       │   ├── markitdown_backend.py
│       │   ├── mathpix_backend.py
│       │   ├── tabula_backend.py
│       │   └── builtin_backend.py   # Python stdlib conversions (json, csv, strip, etc.)
│       └── utils/
│           ├── __init__.py
│           ├── logging_config.py    # Structured JSON logging setup
│           └── formats.py           # Format enum and extension mapping
├── tests/
│   ├── __init__.py
│   ├── test_detector.py
│   ├── test_router.py
│   ├── test_converter.py
│   └── fixtures/               # Sample files for each format
│       ├── sample.pdf
│       ├── sample.docx
│       ├── sample.md
│       └── ...
├── logs/                       # Runtime logs (gitignored)
├── output/                     # Default output directory (gitignored)
└── docs/
    ├── prd.md
    └── tech-spec-mvp.md
```

## 2. Dependencies

### pyproject.toml

```toml
[project]
name = "doc-shape-shifter"
version = "0.1.0"
description = "Intelligent document format converter with automatic backend selection"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "Jon Chun", email = "jonchun2000@gmail.com"}]

dependencies = [
    "click>=8.1",
    "python-magic>=0.4.27",
    "pymupdf>=1.24",
    "rich>=13.0",
]

[project.optional-dependencies]
pandoc = ["pypandoc>=1.13"]
docling = ["docling>=2.82.0"]
markitdown = ["markitdown[all]>=0.1.5"]
tabula = ["tabula-py>=2.9"]
mathpix = ["requests>=2.31"]
all = [
    "doc-shape-shifter[pandoc,docling,markitdown,tabula,mathpix]",
]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
]

[project.scripts]
dss = "doc_shape_shifter.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### System Dependencies

| Dependency | Install Command | Required For |
|---|---|---|
| Pandoc ≥ 3.1 | `brew install pandoc` | Most format bridges |
| Java Runtime | `brew install openjdk` | tabula-py (PDF table extraction) |
| libmagic | `brew install libmagic` | python-magic MIME detection |

## 3. Module Specifications

### 3.1 `formats.py` — Format Registry

```python
from enum import Enum

class DocFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"
    PLAIN_TEXT = "txt"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    LATEX = "latex"
    EPUB = "epub"
    RTF = "rtf"

# Extension → Format mapping (multiple extensions per format)
EXTENSION_MAP: dict[str, DocFormat] = {
    ".pdf": DocFormat.PDF,
    ".docx": DocFormat.DOCX,
    ".md": DocFormat.MARKDOWN,
    ".markdown": DocFormat.MARKDOWN,
    ".txt": DocFormat.PLAIN_TEXT,
    ".text": DocFormat.PLAIN_TEXT,
    ".html": DocFormat.HTML,
    ".htm": DocFormat.HTML,
    ".json": DocFormat.JSON,
    ".csv": DocFormat.CSV,
    ".tex": DocFormat.LATEX,
    ".latex": DocFormat.LATEX,
    ".epub": DocFormat.EPUB,
    ".rtf": DocFormat.RTF,
}

# Format → canonical extension
FORMAT_EXTENSION: dict[DocFormat, str] = {
    DocFormat.PDF: ".pdf",
    DocFormat.DOCX: ".docx",
    DocFormat.MARKDOWN: ".md",
    DocFormat.PLAIN_TEXT: ".txt",
    DocFormat.HTML: ".html",
    DocFormat.JSON: ".json",
    DocFormat.CSV: ".csv",
    DocFormat.LATEX: ".tex",
    DocFormat.EPUB: ".epub",
    DocFormat.RTF: ".rtf",
}
```

### 3.2 `detector.py` — Format Detection

**Responsibilities**: Determine the true format of an input file using a layered strategy.

**Detection Order**:
1. `python-magic` MIME type (most reliable)
2. File extension fallback
3. Content heuristics (e.g., check for `%PDF-` header, `\documentclass` for LaTeX)

**Interface**:
```python
def detect_format(file_path: Path) -> DocFormat:
    """Detect document format. Raises UnsupportedFormatError if unknown."""
```

### 3.3 `router.py` — Conversion Matrix & Backend Selection

**Core Data Structure**: A nested dict mapping `(source_format, target_format)` to an ordered list of backend names (fallback chain).

```python
# Type: dict[tuple[DocFormat, DocFormat], list[str]]
CONVERSION_MATRIX = {
    (DocFormat.PDF, DocFormat.DOCX):      ["pandoc", "docling"],
    (DocFormat.PDF, DocFormat.MARKDOWN):   ["docling", "pymupdf", "pandoc"],
    (DocFormat.PDF, DocFormat.PLAIN_TEXT): ["pymupdf", "pandoc"],
    (DocFormat.PDF, DocFormat.HTML):       ["docling", "pandoc"],
    (DocFormat.PDF, DocFormat.JSON):       ["docling"],
    (DocFormat.PDF, DocFormat.CSV):        ["tabula"],
    (DocFormat.PDF, DocFormat.LATEX):      ["mathpix", "pandoc"],
    (DocFormat.PDF, DocFormat.EPUB):       ["pandoc"],
    (DocFormat.PDF, DocFormat.RTF):        ["pandoc"],

    (DocFormat.DOCX, DocFormat.PDF):       ["pandoc"],
    (DocFormat.DOCX, DocFormat.MARKDOWN):  ["markitdown", "docling", "pandoc"],
    (DocFormat.DOCX, DocFormat.PLAIN_TEXT):["docling", "pandoc"],
    (DocFormat.DOCX, DocFormat.HTML):      ["docling", "pandoc"],
    (DocFormat.DOCX, DocFormat.JSON):      ["markitdown"],
    (DocFormat.DOCX, DocFormat.LATEX):     ["pandoc"],
    (DocFormat.DOCX, DocFormat.EPUB):      ["pandoc"],
    (DocFormat.DOCX, DocFormat.RTF):       ["pandoc"],

    (DocFormat.MARKDOWN, DocFormat.PDF):       ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.DOCX):      ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.PLAIN_TEXT): ["builtin"],
    (DocFormat.MARKDOWN, DocFormat.HTML):       ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.JSON):       ["markitdown"],
    (DocFormat.MARKDOWN, DocFormat.LATEX):      ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.EPUB):       ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.RTF):        ["pandoc"],

    (DocFormat.HTML, DocFormat.PDF):        ["pandoc"],
    (DocFormat.HTML, DocFormat.DOCX):       ["pandoc"],
    (DocFormat.HTML, DocFormat.MARKDOWN):   ["docling", "pandoc"],
    (DocFormat.HTML, DocFormat.PLAIN_TEXT): ["builtin", "pandoc"],
    (DocFormat.HTML, DocFormat.JSON):       ["docling"],
    (DocFormat.HTML, DocFormat.CSV):        ["builtin"],
    (DocFormat.HTML, DocFormat.LATEX):      ["pandoc"],
    (DocFormat.HTML, DocFormat.EPUB):       ["pandoc"],
    (DocFormat.HTML, DocFormat.RTF):        ["pandoc"],

    # ... remaining pairs follow the same pattern from the PRD matrix
}
```

**Interface**:
```python
def get_backend_chain(source: DocFormat, target: DocFormat) -> list[str]:
    """Return ordered list of backend names for this conversion pair.
    Raises UnsupportedConversionError if no path exists."""

def get_best_available_backend(source: DocFormat, target: DocFormat) -> str:
    """Return the first backend in the chain that is actually installed."""
```

### 3.4 `backends/base.py` — Backend Abstract Base Class

```python
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ConversionResult:
    success: bool
    output_path: Path | None
    backend_name: str
    duration_seconds: float
    source_format: str
    target_format: str
    error_message: str | None = None
    file_size_bytes: int | None = None

class BaseBackend(ABC):
    name: str  # e.g., "pandoc", "docling"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend's dependencies are installed."""

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path,
                source_format: str, target_format: str) -> ConversionResult:
        """Execute the conversion. Returns ConversionResult."""

    def supported_pairs(self) -> set[tuple[str, str]]:
        """Return set of (source, target) format pairs this backend handles."""
```

### 3.5 Backend Implementations

#### `pandoc_backend.py`
- Uses `pypandoc` library (or shells out to `pandoc` CLI)
- Handles the largest number of format pairs (the "universal bridge")
- Checks `pandoc --version` for availability

#### `docling_backend.py`
- Uses `docling` Python API
- Best for: PDF→MD, PDF→JSON, PDF→HTML, DOCX→MD (layout-aware)
- Higher resource usage; optional install

#### `pymupdf_backend.py`
- Uses `pymupdf` (fitz) for fast native PDF text extraction
- Best for: PDF→TXT (fastest), PDF→MD (basic)
- Lightweight, always available

#### `markitdown_backend.py`
- Uses Microsoft's `markitdown` library
- Best for: DOCX→MD, EPUB→MD, RTF→MD, JSON→MD, CSV→MD
- Broad input support, markdown-only output

#### `mathpix_backend.py`
- Uses Mathpix REST API (requires API key in .env)
- Best for: PDF→LaTeX (especially math-heavy documents)
- Gracefully disabled when no API key is present

#### `tabula_backend.py`
- Uses `tabula-py` (Java-based)
- Best for: PDF→CSV (table extraction)
- Requires Java runtime

#### `builtin_backend.py`
- Pure Python conversions using stdlib
- Handles: MD→TXT (strip markdown), HTML→TXT (html.parser), JSON→CSV (pandas/csv), etc.
- Always available, no external deps

### 3.6 `converter.py` — Main Orchestration

```python
def convert(
    input_path: str | Path,
    output_path: str | Path | None = None,
    target_format: str | None = None,
    backend: str | None = None,  # Force specific backend
    fallback: bool = True,       # Try next backend on failure
) -> ConversionResult:
    """
    Main entry point.

    1. Detect source format from input_path
    2. Determine target format from output_path extension or target_format arg
    3. Look up backend chain from router
    4. Execute first available backend (or forced backend)
    5. On failure, try next in chain if fallback=True
    6. Return ConversionResult with metadata
    """
```

### 3.7 `cli.py` — Command-Line Interface

```python
@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path(), required=False)
@click.option("-t", "--to", "target_format", help="Target format (pdf, docx, md, txt, ...)")
@click.option("-b", "--backend", help="Force a specific backend")
@click.option("--no-fallback", is_flag=True, help="Don't try alternate backends on failure")
@click.option("--list-backends", is_flag=True, help="List installed backends and exit")
@click.option("--list-formats", is_flag=True, help="List supported format pairs and exit")
@click.option("-v", "--verbose", count=True, help="Increase log verbosity (-v, -vv)")
def main(...):
    """Convert documents between formats.

    Examples:
        dss report.pdf report.md
        dss paper.tex --to docx
        dss data.csv --to json
        dss document.docx --to md --backend markitdown
    """
```

### 3.8 `logging_config.py` — Structured Logging

```python
import logging
import json
from datetime import datetime

# JSON structured log format for machine readability
# Logs to both console (Rich) and file (JSON lines)
# Fields: timestamp, level, event, source_format, target_format,
#         backend, duration_s, file_size_bytes, error
```

## 4. Backend Selection Logic (Decision Flow)

```
Input File
    │
    ▼
detect_format(file) → source_format
    │
    ▼
Determine target_format (from --to flag or output extension)
    │
    ▼
get_backend_chain(source, target) → ["backend_a", "backend_b", ...]
    │
    ▼
For each backend in chain:
    ├─ backend.is_available()?
    │   ├─ NO → skip, log warning
    │   └─ YES → backend.convert(input, output)
    │       ├─ SUCCESS → return ConversionResult(success=True)
    │       └─ FAILURE → log error, continue to next
    │
    ▼
All backends failed → return ConversionResult(success=False, error=...)
```

## 5. Error Handling Strategy

| Scenario | Behavior |
|---|---|
| Backend not installed | Skip silently (DEBUG log), try next |
| Backend raises exception | Log ERROR with traceback, try next |
| All backends fail | Return error result, CLI exits with code 1 |
| Unsupported format pair | Raise `UnsupportedConversionError` with suggestion |
| Input file not found | Click handles this (type=Path(exists=True)) |
| Pandoc not installed system-wide | Log clear install instructions |

## 6. Logging Specification

**Log Levels**:
- `INFO`: Conversion started, backend selected, conversion completed
- `WARNING`: Backend skipped (not installed), fallback triggered
- `ERROR`: Backend failed, all backends exhausted
- `DEBUG`: MIME detection details, backend availability checks

**Log File**: `logs/dss_{date}.jsonl` (one JSON object per line)

**Example log entry**:
```json
{
  "timestamp": "2026-03-31T14:22:05.123Z",
  "level": "INFO",
  "event": "conversion_complete",
  "source_format": "pdf",
  "target_format": "md",
  "backend": "docling",
  "duration_s": 2.34,
  "input_file": "report.pdf",
  "output_file": "report.md",
  "file_size_bytes": 1048576
}
```

## 7. Testing Plan

| Test Category | Coverage |
|---|---|
| **Unit: detector** | MIME detection for all 10 formats; extension fallback; heuristic detection |
| **Unit: router** | All valid pairs return a chain; invalid pairs raise error; installed-only filtering |
| **Unit: backends** | Each backend's `is_available()` and `convert()` with fixture files |
| **Integration** | End-to-end CLI conversion for top 10 most common pairs |
| **Edge cases** | Empty files, large files (>100MB), files with wrong extension |

## 8. Implementation Order

1. `formats.py` + `detector.py` — Foundation
2. `backends/base.py` + `backends/builtin_backend.py` — Always-available conversions
3. `backends/pymupdf_backend.py` — Fast PDF text extraction
4. `backends/pandoc_backend.py` — The universal bridge
5. `router.py` — Wire up the conversion matrix
6. `converter.py` — Orchestration with fallback
7. `cli.py` — User-facing CLI
8. `backends/docling_backend.py` — AI-powered parsing (optional)
9. `backends/markitdown_backend.py` — Microsoft converter (optional)
10. `backends/tabula_backend.py` + `backends/mathpix_backend.py` — Specialists
11. `logging_config.py` — Structured logging
12. Tests
