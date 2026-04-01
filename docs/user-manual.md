# User Manual

## Purpose

This manual explains how to install, configure, run, and interpret `doc-shape-shifter` on a local Mac, with specific attention to an Apple Silicon MacBook Pro M4 environment.

## Before You Start

Recommended baseline:

- macOS on Apple Silicon
- Homebrew installed
- Git installed
- `uv` available
- `pandoc` available
- Java available
- either `tectonic` or `pdflatex` available for PDF rendering

## Installation

### Clone The Repository

```bash
mkdir -p ~/code
git clone https://github.com/jon-chun/doc-shape-shifter.git ~/code/doc-shape-shifter
cd ~/code/doc-shape-shifter
```

### Install System Dependencies

```bash
brew install pandoc openjdk uv tectonic
```

If you already use TeX Live, `pdflatex` can serve as the Pandoc PDF engine instead of `tectonic`.

### Create The Virtual Environment

```bash
uv venv --python 3.12 .venv
uv sync --extra dev
```

### Validate The Environment

```bash
uv run doc-shape-shifter doctor
```

## Configuration

### Optional Mathpix Setup

Mathpix is not required for the current MVP, but the environment variable names are:

```bash
export MATHPIX_APP_ID="your-app-id"
export MATHPIX_APP_KEY="your-app-key"
```

The project includes `.env.example` as a reminder of the expected keys.

## Daily Workflow

### 1. Inspect The Environment

Run:

```bash
uv run doc-shape-shifter doctor
```

Interpretation:

- `available=yes` means the tool can be used now.
- `available=no` means that route is unavailable.
- `pdf_engine` confirms whether Pandoc can render PDFs.

### 2. Preview The Conversion Route

Run:

```bash
uv run doc-shape-shifter plan input.pdf output.docx
```

This is the safest way to understand what the tool will do before conversion.

### 3. Run The Conversion

Examples:

```bash
uv run doc-shape-shifter convert input.pdf output.md
uv run doc-shape-shifter convert input.docx output.html
uv run doc-shape-shifter convert input.md output.pdf
uv run doc-shape-shifter convert input.pdf output.csv
```

### 4. Force OCR-Oriented Handling When Needed

For scanned or poor-quality PDFs:

```bash
uv run doc-shape-shifter convert scan.pdf scan.md --force-ocr
```

### 5. Influence The Route Ranking

If you want to bias the planner:

```bash
uv run doc-shape-shifter plan input.pdf output.docx --prefer-engine docling
```

This boosts the named engine. It does not guarantee that the engine will be selected if the route is invalid.

## Understanding The Output

### `doctor` Output

Example categories:

- `pandoc`: text-like conversion support
- `docling`: broad document parsing
- `pymupdf4llm`: PDF Markdown extraction
- `tabula`: PDF table extraction
- `mathpix`: optional cloud OCR specialist
- `pdf_engine`: PDF writing capability through Pandoc

### `plan` Output

Each route shows:

- route name
- route score
- engine per step
- action per step

Higher scores rank first. The selected route is usually the first one unless execution fails.

### `convert` Output

The command prints:

- selected route
- output location

If conversion fails, the tool aggregates attempted route errors into one message.

## Practical Examples

### Convert Markdown To PDF

```bash
uv run doc-shape-shifter convert notes.md notes.pdf
```

This usually routes directly through Pandoc.

### Convert DOCX To Markdown

```bash
uv run doc-shape-shifter convert report.docx report.md
```

This typically uses direct Pandoc conversion.

### Convert PDF To CSV

```bash
uv run doc-shape-shifter convert tables.pdf tables.csv
```

This is table-oriented extraction through `tabula-py`.

### Convert PDF To DOCX

```bash
uv run doc-shape-shifter convert paper.pdf paper.docx
```

This usually extracts Markdown first, then renders with Pandoc.

## Troubleshooting

### `pandoc` Missing

Install it:

```bash
brew install pandoc
```

### PDF Output Fails

Check:

- `uv run doc-shape-shifter doctor`
- whether `tectonic` or `pdflatex` is installed
- whether Pandoc alone can render a simple Markdown file to PDF

### `tabula` Route Unavailable

Check Java:

```bash
java -version
```

Then rerun:

```bash
uv run doc-shape-shifter doctor
```

### `Mathpix` Unavailable

That is expected unless you intentionally configured credentials.

## Development Commands

Run tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check
```

Run as a Python module:

```bash
uv run python -m doc_shape_shifter doctor
```

## Building A Release Zip

To create a clean archive of the project tree:

```bash
bash ./scripts/build_release_zip.sh
```

The generated archive is written to `dist/`.
