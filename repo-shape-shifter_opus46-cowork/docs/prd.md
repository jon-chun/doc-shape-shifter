# Product Requirements Document: Doc-Shape-Shifter

**Version**: 1.0
**Date**: 2026-03-31
**Author**: Jon Chun
**Status**: Draft

---

## 1. Problem Statement

Researchers and developers working with AI pipelines (RAG, agent workflows, multimodal analysis) must frequently convert documents between formats. The current landscape is fragmented: no single tool handles all conversions well, and selecting the right tool for a given source-target pair requires deep domain knowledge. Users waste significant time manually choosing between Pandoc, Docling, PyMuPDF, MarkItDown, Mathpix, and dozens of other tools — each with different strengths, limitations, and installation requirements.

**Doc-Shape-Shifter** is a unified CLI and Python library that automatically selects the best conversion backend for any given source-to-target format pair and executes it transparently.

## 2. Target Users

- AI/ML researchers building RAG pipelines who need to ingest diverse document types into markdown/JSON
- Data engineers processing mixed-format document batches
- Academics converting papers between LaTeX, PDF, DOCX, and Markdown
- Developers building document processing microservices

## 3. Goals

1. **Unified Interface**: Single CLI command and Python API to convert between any supported format pair
2. **Intelligent Routing**: Automatically select the best backend tool based on the source format, target format, and content characteristics (e.g., math-heavy, table-heavy, scanned)
3. **Modular Backends**: Each conversion backend is a plugin that can be installed independently
4. **Quality Awareness**: Report conversion confidence and optionally trigger fallback chains
5. **Local-First**: All core conversions run locally without API keys; cloud backends are opt-in

## 4. Supported Formats (Full Vision)

### Tier 1 — MVP (Core text/document formats)
PDF (native), DOCX, Markdown, Plain Text, HTML, LaTeX, JSON, CSV, EPUB, RTF

### Tier 2 — Phase 2 (Office and structured data)
PPTX, XLSX, XML, ODT

### Tier 3 — Phase 3 (Media and specialized)
PNG/JPG (OCR), SVG, PDF (scanned), Audio transcription

## 5. Conversion Strategy

The system uses a **Router-Worker** architecture derived from the survey's Section 10 recommendation:

1. **Format Detection**: Use `python-magic` or Magika for MIME-type detection independent of file extension
2. **Route Selection**: A conversion matrix maps each (source, target) pair to a ranked list of backends
3. **Backend Execution**: The highest-priority installed backend is invoked
4. **Fallback Chain**: If the primary backend fails or produces low-confidence output, the next backend in the ranked list is tried

### Conversion Matrix (Primary Backend Selection)

Based on the survey's Section 4 matrix, the first-line tools for Tier 1 formats are:

| Source → Target | PDF | DOCX | MD | TXT | HTML | JSON | CSV | LaTeX | EPUB | RTF |
|---|---|---|---|---|---|---|---|---|---|---|
| **PDF** | — | Pandoc | Docling | PyMuPDF | Docling | Docling | Tabula | Mathpix | Pandoc | Pandoc |
| **DOCX** | Pandoc | — | MarkItDown | Docling | Docling | MarkItDown | — | Pandoc | Pandoc | Pandoc |
| **Markdown** | Pandoc | Pandoc | — | strip | Pandoc | MarkItDown | — | Pandoc | Pandoc | Pandoc |
| **Plain Text** | Pandoc | Pandoc | wrap | — | Pandoc | wrap | — | — | — | Pandoc |
| **HTML** | Pandoc | Pandoc | Docling | html2text | — | Docling | BS4 | Pandoc | Pandoc | Pandoc |
| **JSON** | — | — | MarkItDown | jq | Docling | — | Pandas | — | — | — |
| **CSV** | — | — | MarkItDown | Pandas | — | Pandas | — | — | — | — |
| **LaTeX** | Pandoc | Pandoc | Docling | detex | Pandoc | — | — | — | Pandoc | — |
| **EPUB** | Pandoc | Pandoc | MarkItDown | epub2txt | Pandoc | — | — | — | — | — |
| **RTF** | Pandoc | Pandoc | MarkItDown | rtf2txt | Pandoc | MarkItDown | — | — | — | — |

## 6. Backend Library Overview

| Backend | Role | License | Install |
|---|---|---|---|
| **Pandoc** | Universal format bridge (30+ formats) | GPL-2.0 | `brew install pandoc` |
| **Docling** | AI-powered layout-aware parsing (PDF, DOCX, HTML → MD/JSON) | MIT | `pip install docling` |
| **PyMuPDF** | Fast native PDF text extraction | AGPL | `pip install pymupdf` |
| **MarkItDown** | Microsoft's lightweight multi-format → Markdown | MIT | `pip install markitdown[all]` |
| **Mathpix** | Math/LaTeX specialist (commercial API) | Commercial | `pip install mathpix` |
| **Tabula** | PDF table extraction to CSV/JSON | MIT | `pip install tabula-py` |
| **python-magic** | MIME type detection | MIT | `pip install python-magic` |

## 7. Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────┐
│  CLI / API   │───▶│ MIME Detect   │───▶│ Route Selector  │───▶│ Backend  │
│  (click)     │    │ (magic/ext)   │    │ (matrix lookup) │    │ Worker   │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────┘
                                              │                     │
                                              ▼                     ▼
                                       ┌────────────┐       ┌───────────┐
                                       │ Fallback    │       │ Output    │
                                       │ Chain       │       │ File      │
                                       └────────────┘       └───────────┘
```

## 8. Non-Functional Requirements

- **Performance**: Common conversions (PDF→MD, DOCX→MD) complete in <5s for typical documents (<50 pages)
- **Memory**: Core operation within 8GB RAM; GPU backends optional
- **Platform**: macOS (Apple Silicon primary), Linux, Windows
- **Python**: 3.10+ required (Docling requirement)
- **Logging**: Structured JSON logs with conversion metadata (source format, target format, backend used, duration, file size)
- **Error Handling**: Graceful degradation with informative error messages when a backend is not installed

## 9. Success Metrics

- Supports all 90 valid Tier 1 format pairs (10x10 minus 10 identity minus lossy)
- 95%+ of conversions succeed on first backend attempt
- CLI responds with usage help in <1s
- Average conversion time <5s for documents under 50 pages

## 10. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Backend dependency conflicts | Isolate heavy backends (Docling, MinerU) in optional extras groups |
| Pandoc version incompatibilities | Pin minimum Pandoc version; detect at runtime |
| Scanned PDF misclassified as native | MIME detection + heuristic check (text layer present?) |
| Mathpix API key required for LaTeX | Fallback to Pandoc for basic LaTeX; Mathpix is opt-in |

## 11. Roadmap

| Phase | Scope | Timeline |
|---|---|---|
| **MVP (v0.1)** | Tier 1 formats, CLI, Pandoc + Docling + PyMuPDF + MarkItDown | 2-3 weeks |
| **v0.2** | Fallback chains, confidence scoring, batch mode | 2 weeks |
| **v0.3** | Tier 2 formats (PPTX, XLSX, XML, ODT) | 2 weeks |
| **v0.4** | OCR/scanned PDF support (MinerU, Marker) | 3 weeks |
| **v1.0** | FastAPI server, Docker image, full quality loop | 4 weeks |
