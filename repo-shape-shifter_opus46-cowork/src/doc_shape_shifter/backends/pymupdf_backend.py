"""PyMuPDF backend — fast native PDF text extraction."""

import logging
import time
from pathlib import Path

from .base import BaseBackend, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.pymupdf")


class PyMuPDFBackend(BaseBackend):
    """Backend using PyMuPDF (fitz) for PDF text extraction.

    Strengths:
    - Extremely fast for native (non-scanned) PDFs
    - Low resource usage (CPU only)
    - Good for PDF → Plain Text and basic PDF → Markdown

    Limitations:
    - No OCR (scanned PDFs return empty text)
    - Limited structural awareness (no table/heading detection)
    """

    name = "pymupdf"

    def is_available(self) -> bool:
        try:
            import pymupdf  # noqa: F401
            return True
        except ImportError:
            # Try legacy import name
            try:
                import fitz  # noqa: F401
                return True
            except ImportError:
                return False

    def version_info(self) -> str:
        try:
            import pymupdf
            return f"PyMuPDF {pymupdf.__version__}"
        except (ImportError, AttributeError):
            try:
                import fitz
                return f"PyMuPDF (fitz) {fitz.version[0]}"
            except (ImportError, AttributeError):
                return "PyMuPDF (not installed)"

    def _get_fitz(self):
        """Import pymupdf/fitz regardless of package name."""
        try:
            import pymupdf
            return pymupdf
        except ImportError:
            import fitz
            return fitz

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        start = time.time()
        logger.info(
            "pymupdf: converting %s → %s (%s)",
            source_format, target_format, input_path.name,
        )

        if source_format != "pdf":
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=time.time() - start,
                source_format=source_format, target_format=target_format,
                error_message="PyMuPDF only supports PDF as source format",
            )

        if target_format not in ("txt", "md"):
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=time.time() - start,
                source_format=source_format, target_format=target_format,
                error_message=f"PyMuPDF supports PDF → txt/md, not PDF → {target_format}",
            )

        try:
            fitz = self._get_fitz()
            doc = fitz.open(str(input_path))
            total_pages = len(doc)
            logger.debug("pymupdf: opened PDF with %d pages", total_pages)

            text_parts = []
            for i, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
                if (i + 1) % 50 == 0:
                    pct = ((i + 1) / total_pages) * 100
                    logger.debug("pymupdf: processed %d/%d pages (%.0f%%)", i + 1, total_pages, pct)

            doc.close()

            full_text = "\n\n".join(text_parts)
            warnings = []

            if not full_text.strip():
                warnings.append(
                    "No text extracted — this may be a scanned/image-only PDF. "
                    "Consider using docling or marker for OCR."
                )
                logger.warning("pymupdf: no text extracted from %s", input_path.name)

            # For markdown output, add minimal structure
            if target_format == "md":
                # Prefix with source filename as title
                full_text = f"# {input_path.stem}\n\n{full_text}"

            output_path.write_text(full_text, encoding="utf-8")
            duration = time.time() - start
            size = output_path.stat().st_size

            logger.info(
                "pymupdf: extracted %d chars from %d pages in %.2fs",
                len(full_text), total_pages, duration,
                extra={"duration_s": duration, "file_size_bytes": size},
            )

            return ConversionResult(
                success=True,
                output_path=output_path,
                backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format,
                target_format=target_format,
                file_size_bytes=size,
                warnings=warnings,
            )

        except Exception as e:
            duration = time.time() - start
            logger.error("pymupdf: conversion failed: %s", e, exc_info=True)
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=str(e),
            )
