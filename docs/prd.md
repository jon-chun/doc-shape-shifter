# Product Requirements Document

## Product Name

doc-shape-shifter

## Product Summary

`doc-shape-shifter` is a local-first document transformation toolkit that accepts heterogeneous source files, determines the highest-value available conversion path, and outputs a target format with minimal operator decision-making.

The longer-term product direction is broader than document conversion. The repository is intentionally organized so the same package can expand into OCR, OTR, OMR, image enhancement, restoration, denoising, and upscaling workflows without collapsing all responsibilities into one module.

## Problem

Document conversion remains fragmented across specialized tools. The ecosystem survey in `docs/research/gemini3dr_Document Conversion Ecosystem Survey_20260329.md` shows that:

- `Pandoc` is excellent for text-like transforms.
- `Docling` is strong for broad document parsing and complex structure.
- `PyMuPDF4LLM` is the fast path for native-text PDF extraction.
- `Tabula` is the practical local route for PDF tables.
- `Mathpix` is strong for STEM-heavy OCR but introduces an external service dependency.

Users should not need to manually remember which engine is best for each pair.

## Target Users

- Researchers with mixed PDF, DOCX, HTML, Markdown, and spreadsheet corpora.
- AI/RAG builders normalizing source documents into Markdown, JSON, or plain text.
- Developers who want one stable CLI and package API instead of ad hoc scripts.

## Primary Use Cases

- Sync a local repo and bootstrap the toolkit on a MacBook Pro M4.
- Convert a native PDF into Markdown, DOCX, HTML, JSON, or plain text.
- Convert Office and text-like formats through a single CLI.
- Extract table-heavy PDF content to CSV.
- Inspect the planned route before doing real work.

## Product Goals

- Provide a local-first CLI for practical format conversion.
- Prefer open-source local tooling by default.
- Expose route selection transparently.
- Use a repository layout suitable for future packaging and expansion.
- Keep installation and operational guidance understandable without reading source code.

## Non-Goals For The MVP

- Perfect round-trip fidelity for every format pair.
- Full GUI support.
- Full image conversion coverage.
- Distributed batch orchestration.
- Mandatory cloud services.

## Scope

### In Scope

- Package-friendly repository structure.
- `doctor`, `plan`, and `convert` commands.
- Automatic routing across `pandoc`, `docling`, `pymupdf4llm`, and `tabula-py`.
- Optional `Mathpix` credential detection.
- Documentation for installation, configuration, operation, and interpretation.
- Release zip generation for project handoff.

### Out Of Scope

- Full image enhancement or restoration pipelines.
- Optical music recognition implementation.
- Production batch schedulers and review queues.

## Functional Requirements

- Detect source and target formats from extensions or explicit flags.
- Rank available conversion plans.
- Execute the highest-ranked route and fall back on failure.
- Report tool availability and PDF renderer status.
- Support at least the Section 4 first-line formats:
  - `pdf`
  - `docx`
  - `pptx`
  - `xlsx`
  - `html`
  - `json`
  - `csv`
  - `md`
  - `tex`
  - `epub`
  - `txt`

## Quality Requirements

- Installation should be reproducible on Apple Silicon macOS.
- Repo layout should be understandable to a new contributor.
- Tooling should fail clearly when dependencies are missing.
- The codebase should remain easy to extend with new engines.

## Success Criteria

- A user can bootstrap the repo from the README on a new Mac in under 20 minutes.
- A user can inspect the planned route before converting.
- Common flows such as `pdf -> md`, `md -> pdf`, `docx -> html`, and `pdf -> csv` work through one CLI.
- The repo can be published later as a Python package without structural rework.

## Future Expansion Directions

- OCR-specific routing with confidence thresholds.
- OTR pipelines for handwriting or specialized text extraction.
- OMR pipelines for music notation.
- Restoration and enhancement stages before OCR.
- Batch pipelines and workflow orchestration.
