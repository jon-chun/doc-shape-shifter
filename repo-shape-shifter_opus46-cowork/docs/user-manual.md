# Doc-Shape-Shifter User Manual

**Version**: 0.1.0 | **Last Updated**: 2026-03-31

---

## 1. Introduction

Doc-Shape-Shifter (`dss`) is a command-line tool and Python library that converts documents between formats. Instead of learning which tool to use for each conversion (Pandoc for LaTeX-to-DOCX, PyMuPDF for PDF-to-text, Docling for PDF-to-Markdown with layout, etc.), you use a single command and the system chooses the best backend automatically.

### Who Is This For?

- **AI/ML researchers** building RAG pipelines who ingest PDFs, Word docs, and web pages
- **Data engineers** processing mixed-format document batches
- **Academics** converting papers between LaTeX, PDF, DOCX, and Markdown
- **Developers** building document processing services

---

## 2. Installation

### 2.1 System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | macOS 12+, Ubuntu 20.04+, Windows 10+ | macOS 14+ (Apple Silicon) |
| Python | 3.10 | 3.11 |
| RAM | 4 GB | 8 GB+ (16 GB for Docling) |
| Disk | 500 MB | 2 GB (with all backends) |

### 2.2 System Dependencies

```bash
# macOS
brew install pandoc libmagic

# Ubuntu/Debian
sudo apt-get install pandoc libmagic1

# Optional: Java for Tabula (PDF table extraction)
brew install openjdk    # macOS
sudo apt-get install default-jdk   # Ubuntu
```

### 2.3 Python Installation

```bash
git clone https://github.com/jon-chun/doc-shape-shifter.git
cd doc-shape-shifter

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install: choose your level
pip install -e .             # Core only (PyMuPDF, python-magic)
pip install -e ".[pandoc]"   # + Pandoc bridge (most common)
pip install -e ".[all]"      # Everything
```

### 2.4 Verify Installation

```bash
dss --version
dss --list-backends
python scripts/check_backends.py
```

Expected output for a full install:
```
  [OK]   Python: 3.11.x
  [OK]   Pandoc CLI: pandoc 3.x
  [OK]   libmagic: 0.4.27
  [OK]   PyMuPDF: 1.24.x
  [OK]   pypandoc: 1.13
  [OK]   Docling: 2.82.0
  [OK]   MarkItDown: 0.1.5
  [OK]   tabula-py: 2.9.x
  [OK]   Rich: 13.x
  [OK]   Click: 8.x
```

---

## 3. Basic Usage

### 3.1 Converting a File

The simplest form takes an input file and an output file:

```bash
dss report.pdf report.md
```

The system will:
1. Detect that `report.pdf` is a PDF (via MIME type)
2. Determine the target is Markdown (from `.md` extension)
3. Look up the backend chain: `docling -> pymupdf -> pandoc -> markitdown`
4. Try the first available backend
5. Write `report.md` and print a summary

### 3.2 Specifying Target Format

Instead of an output filename, use `--to`:

```bash
dss paper.tex --to docx
# Produces: paper.docx
```

### 3.3 Forcing a Backend

If you want to control which tool is used:

```bash
dss report.pdf report.md --backend pymupdf
```

### 3.4 Disabling Fallback

By default, if a backend fails, the next one in the chain is tried. To disable this:

```bash
dss report.pdf report.md --no-fallback
```

---

## 4. Common Conversion Recipes

### PDF to Markdown (best quality)
```bash
dss paper.pdf paper.md
# Uses Docling (AI layout-aware) if installed, falls back to PyMuPDF
```

### PDF to Plain Text (fastest)
```bash
dss paper.pdf paper.txt
# Uses PyMuPDF for fast native text extraction
```

### PDF Table Extraction
```bash
dss financial-report.pdf tables.csv
# Uses Tabula (requires Java)
```

### LaTeX to Word (for journal submission)
```bash
dss paper.tex paper.docx
# Uses Pandoc
```

### Word to Markdown (for GitHub)
```bash
dss proposal.docx proposal.md
# Uses MarkItDown or Docling
```

### CSV to JSON
```bash
dss data.csv data.json
# Uses builtin Python backend (always available)
```

### HTML to Markdown
```bash
dss webpage.html page.md
# Uses Docling for structural awareness
```

### Batch Conversion (Shell Loop)
```bash
for f in *.pdf; do
    dss "$f" --to md -v
done
```

---

## 5. Format Detection

The detector uses three layers to identify the source format:

1. **MIME type** via `python-magic` (most reliable for binary files like PDF, DOCX, EPUB)
2. **File extension** mapping (fast, covers all common extensions)
3. **Content heuristics** (for files without extensions or with wrong extensions):
   - `%PDF-` header -> PDF
   - `\documentclass` -> LaTeX
   - `<!DOCTYPE html` -> HTML
   - `{\rtf` -> RTF
   - JSON structure -> JSON
   - Comma-separated rows -> CSV
   - Markdown syntax patterns -> Markdown

---

## 6. Backend Reference

### 6.1 builtin (Always Available)

Pure Python conversions using the standard library. Handles:
- Markdown -> Plain Text (strips markdown syntax)
- HTML -> Plain Text (strips tags)
- JSON -> CSV (flattens array of objects)
- CSV -> JSON (parses to array of objects)
- JSON -> Plain Text (pretty-prints)

### 6.2 PyMuPDF (Core Dependency)

Ultra-fast PDF text extraction using the MuPDF library. Best for native (non-scanned) PDFs. Outputs plain text or basic markdown.

**Limitation**: No OCR capability; scanned PDFs produce empty output with a warning.

### 6.3 Pandoc (Recommended)

The universal format bridge, supporting 30+ formats. Handles most conversions adequately. Required for any conversion involving PDF output, LaTeX, EPUB, RTF, or DOCX output.

**Install**: `brew install pandoc` + `pip install -e ".[pandoc]"`

### 6.4 Docling (Optional, AI-Powered)

IBM Research's layout-aware document parser. Uses the Heron layout model and TableFormer for high-fidelity conversion that preserves headings, tables, and lists.

**Best for**: PDF -> Markdown, PDF -> JSON, DOCX -> Markdown, HTML -> Markdown
**Install**: `pip install -e ".[docling]"`
**Resource**: Higher RAM/CPU usage; GPU optional

### 6.5 MarkItDown (Optional)

Microsoft's lightweight converter. Broad input support (DOCX, XLSX, PPTX, HTML, PDF, EPUB, RTF) but only outputs Markdown.

**Install**: `pip install -e ".[markitdown]"`

### 6.6 Tabula (Optional)

PDF table extraction to CSV and JSON. Requires Java runtime.

**Install**: `pip install -e ".[tabula]"` + `brew install openjdk`

### 6.7 Mathpix (Optional, API)

Commercial API for converting math-heavy PDFs and images to LaTeX. Requires API credentials.

**Install**: `pip install -e ".[mathpix]"` + set `MATHPIX_APP_ID` and `MATHPIX_APP_KEY` in `.env`

---

## 7. Logging and Debugging

### 7.1 Console Verbosity

```bash
dss report.pdf report.md           # Warnings only
dss report.pdf report.md -v        # INFO: see backend selection
dss report.pdf report.md -vv       # DEBUG: full trace
```

### 7.2 Log Files

Every run appends to `logs/dss_YYYYMMDD.jsonl`. Each line is a JSON object with:

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 UTC timestamp |
| `level` | INFO, WARNING, ERROR, DEBUG |
| `message` | Human-readable description |
| `source_format` | Detected input format |
| `target_format` | Requested output format |
| `backend` | Backend that handled the conversion |
| `duration_s` | Time in seconds |
| `file_size_bytes` | Output file size |
| `error` | Error message (if failed) |

### 7.3 Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| "No text extracted" warning | Scanned/image-only PDF | Install Docling or wait for OCR pipeline (v0.4) |
| "pandoc: command not found" | Pandoc not installed | `brew install pandoc` |
| "UnsupportedFormatError" | File extension not recognized | Use `--to` flag to specify format explicitly |
| Empty output file | Backend produced no content | Try a different backend with `--backend` |
| Java errors with tabula | Java not installed | `brew install openjdk` |
| Mathpix timeout | API connectivity issue | Check API keys in `.env`; check network |

---

## 8. Python API Reference

### convert()

```python
from doc_shape_shifter.converter import convert

result = convert(
    input_path="report.pdf",       # str or Path
    output_path="report.md",       # str, Path, or None (auto-generated)
    target_format="md",            # str or None (inferred from output_path)
    backend=None,                  # str or None (auto-select)
    fallback=True,                 # bool (try alternates on failure)
)
```

### detect_format()

```python
from doc_shape_shifter.detector import detect_format
fmt = detect_format("mystery.dat")  # Returns DocFormat enum
```

### list_backends()

```python
from doc_shape_shifter.backends import list_backends
for name, available in list_backends():
    print(f"{name}: {'yes' if available else 'no'}")
```

### get_backend_chain()

```python
from doc_shape_shifter.router import get_backend_chain
from doc_shape_shifter.utils.formats import DocFormat

chain = get_backend_chain(DocFormat.PDF, DocFormat.MARKDOWN)
# Returns: ["docling", "pymupdf", "pandoc", "markitdown"]
```

---

## 9. FAQ

**Q: Do I need all backends installed?**
No. The core install (PyMuPDF + python-magic) handles PDF->text and the builtin backend handles JSON/CSV/HTML/Markdown transformations. Adding Pandoc covers most remaining pairs. Install additional backends as needed.

**Q: Can I use this in a Docker container?**
Not yet officially, but the package installs cleanly in any Python 3.10+ environment. A Dockerfile will ship with v1.0.

**Q: How does it compare to just using Pandoc?**
Pandoc is excellent for format bridging but limited for layout-aware PDF parsing. Doc-Shape-Shifter uses Pandoc as one of many backends and routes to specialized tools (Docling, PyMuPDF, Tabula) when they produce better results.

**Q: What about scanned PDFs?**
The MVP (v0.1) handles native-text PDFs only. The OCR pipeline (v0.4) will add support via MinerU, Marker, and Surya OCR.

