# Technical Specification

## Overview

The MVP implements a router-based conversion CLI that selects among a small set of concrete tools, balancing fidelity, local availability, and implementation complexity.

## Repository Architecture

```text
src/doc_shape_shifter/
├── __main__.py
├── cli.py
├── core/
│   ├── runtime.py
│   ├── router.py
│   └── types.py
├── engines/
│   └── adapters.py
├── ocr/
├── otr/
├── omr/
├── restoration/
└── pipelines/
```

### Design Intent

- `core/` owns format models, runtime inspection, and route planning.
- `engines/` owns concrete tool adapters.
- `ocr/`, `otr/`, `omr/`, `restoration/`, and `pipelines/` reserve clean namespaces for future feature areas.

## Core Concepts

### Conversion Request

The request model contains:

- input path
- output path
- source format
- target format
- `force_ocr`
- `prefer_engine`

### Intermediate Representation

When a direct conversion is not preferred, the router normalizes the source into an intermediate representation containing:

- source path
- source format
- Markdown
- plain text
- HTML
- table data
- metadata

This keeps the MVP small while still enabling multi-step conversions.

## Engine Responsibilities

### Pandoc

Use for:

- direct text-like conversions
- final rendering from Markdown into `docx`, `pdf`, `html`, `epub`, `tex`, or `txt`
- extracting Markdown from supported text-like inputs

### PyMuPDF4LLM

Use for:

- native-text PDF extraction into Markdown

### Docling

Use for:

- broader PDF and Office ingestion
- fallback parsing when the fast PDF path is insufficient

### tabula-py

Use for:

- `pdf -> csv`
- table-centric PDF extraction

### Mathpix

Reserved for:

- future math-heavy OCR and notation-heavy conversion paths

## Routing Strategy

### Preferred Direct Routes

- same-format copy
- `pdf -> csv` through `tabula-py`
- `md/html/docx/epub/latex/csv -> docx/pdf/html/epub/md/txt/tex` through direct `pandoc`

### Preferred Extract Then Render Routes

- `pdf -> md/txt/html/json` through `pymupdf4llm`, fallback `docling`
- `pdf -> docx/pdf/epub/tex` through extracted Markdown plus `pandoc`
- `pptx/xlsx -> md/txt/json` through `docling`
- `json/csv/html/txt -> rich outputs` through native or Pandoc-backed rendering

## CLI Commands

### `doctor`

Reports:

- tool availability
- optional service credentials
- usable PDF engine status

### `plan`

Prints ranked routes with scores and step details before any file is written.

### `convert`

Executes the best-ranked route, then falls back automatically if needed.

## Packaging Notes

- Uses `src/` layout for import correctness and PyPI readiness.
- Exposes console scripts `doc-shape-shifter` and `dss`.
- Includes documentation, scripts, and tests in the source distribution.

## Verification Strategy

- unit tests for router ranking
- linting with Ruff
- smoke conversions through the CLI

## Risks And Limits

- `Docling` has a heavier dependency footprint than the rest of the stack.
- `pdf -> csv` is not a general semantic document conversion route.
- Some format pairs are lossy by nature and should be treated as best-effort transforms.
