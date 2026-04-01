"""Docling backend — AI-powered layout-aware document parsing (IBM Research)."""

import logging
import time
from pathlib import Path

from .base import BaseBackend, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.docling")


class DoclingBackend(BaseBackend):
    """Backend using IBM's Docling for high-fidelity document conversion."""

    name = "docling"

    def is_available(self) -> bool:
        try:
            import docling  # noqa: F401
            return True
        except ImportError:
            return False

    def version_info(self) -> str:
        try:
            import docling
            return f"docling {getattr(docling, '__version__', 'unknown')}"
        except ImportError:
            return "docling (not installed)"

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        start = time.time()
        logger.info(
            "docling: converting %s -> %s (%s)",
            source_format, target_format, input_path.name,
        )

        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            logger.debug("docling: DocumentConverter initialized")

            result = converter.convert(str(input_path))
            logger.debug("docling: document converted, exporting to %s", target_format)

            if target_format == "md":
                content = result.document.export_to_markdown()
            elif target_format == "json":
                import json
                content = json.dumps(
                    result.document.export_to_dict(), indent=2, ensure_ascii=False
                )
            elif target_format == "html":
                content = result.document.export_to_html()
            elif target_format == "txt":
                content = result.document.export_to_markdown()
                import re
                content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
                content = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", content)
                content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
            else:
                return ConversionResult(
                    success=False, output_path=None, backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format, target_format=target_format,
                    error_message=f"Docling does not support output format: {target_format}",
                )

            output_path.write_text(content, encoding="utf-8")
            duration = time.time() - start
            size = output_path.stat().st_size

            logger.info(
                "docling: conversion complete in %.2fs (%d bytes)",
                duration, size,
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
            )

        except ImportError as e:
            duration = time.time() - start
            logger.warning("docling: import error -- %s", e)
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=f"Docling not installed: {e}. Install with: pip install docling",
            )

        except Exception as e:
            duration = time.time() - start
            logger.error("docling: conversion failed: %s", e, exc_info=True)
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=str(e),
            )
