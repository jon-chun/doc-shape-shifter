"""Concrete engine adapters used by the conversion router."""

from .adapters import (
    convert_pdf_to_csv_with_tabula,
    convert_with_pandoc_direct,
    detect_tooling,
    extract_with_docling,
    extract_with_native,
    extract_with_pandoc,
    extract_with_pymupdf,
    render_with_native,
    render_with_pandoc_from_ir,
)

__all__ = [
    "convert_pdf_to_csv_with_tabula",
    "convert_with_pandoc_direct",
    "detect_tooling",
    "extract_with_docling",
    "extract_with_native",
    "extract_with_pandoc",
    "extract_with_pymupdf",
    "render_with_native",
    "render_with_pandoc_from_ir",
]
