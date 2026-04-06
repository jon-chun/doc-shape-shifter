# Changelog

All notable changes to this project will follow [Keep a Changelog](https://keepachangelog.com/) format.

## [0.1.0] - 2026-03-31

### Added
- Initial MVP release
- CLI entry point (`dss`) with Click
- Format detection via MIME type, file extension, and content heuristics
- Conversion matrix router with ordered fallback chains
- Seven backends: builtin, PyMuPDF, Pandoc, Docling, MarkItDown, Tabula, Mathpix
- Tier 1 format support: PDF, DOCX, Markdown, Plain Text, HTML, JSON, CSV, LaTeX, EPUB, RTF
- Structured JSON logging to `logs/`
- `--list-backends` and `--list-formats` diagnostic commands
- Unit tests for detector, router, and converter modules
- PyPI-ready packaging via Hatch with optional dependency groups

### Future
- Tier 2 formats: PPTX, XLSX, XML, ODT
- Scanned PDF / OCR pipeline (MinerU, Marker, Surya)
- Image enhancement / restoration pipeline
- Optical Music Recognition (OMR) pipeline
- Batch processing mode
- FastAPI server mode
