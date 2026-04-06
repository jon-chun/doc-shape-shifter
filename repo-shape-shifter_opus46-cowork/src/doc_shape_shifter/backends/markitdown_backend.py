"""MarkItDown backend — Microsoft's lightweight multi-format → Markdown converter."""

import logging
import time
from pathlib import Path

from .base import BaseBackend, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.markitdown")


class MarkItDownBackend(BaseBackend):
    """Backend using Microsoft's MarkItDown for converting various formats to Markdown.

    Strengths:
    - Broad input format support (DOCX, XLSX, PPTX, HTML, PDF, EPUB, RTF, etc.)
    - Lightweight and fast
    - Good for quick text extraction

    Limitations:
    - Output is Markdown only (no other target formats)
    - Less structural fidelity than Docling for complex layouts
    - Optional install: pip install markitdown[all]
    """

    name = "markitdown"

    def is_available(self) -> bool:
        try:
            from markitdown import MarkItDown  # noqa: F401
            return True
        except ImportError:
            return False

    def version_info(self) -> str:
        try:
            import markitdown
            return f"markitdown {getattr(markitdown, '__version__', 'unknown')}"
        except ImportError:
            return "markitdown (not installed)"

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        start = time.time()
        logger.info(
            "markitdown: converting %s → %s (%s)",
            source_format, target_format, input_path.name,
        )

        # MarkItDown only outputs markdown (and by extension, plain text via stripping)
        if target_format not in ("md", "txt", "json"):
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=time.time() - start,
                source_format=source_format, target_format=target_format,
                error_message=f"MarkItDown only outputs md/txt/json, not {target_format}",
            )

        try:
            from markitdown import MarkItDown

            md = MarkItDown()
            result = md.convert(str(input_path))
            content = result.text_content

            if not content or not content.strip():
                logger.warning("markitdown: empty output for %s", input_path.name)
                return ConversionResult(
                    success=False, output_path=None, backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format, target_format=target_format,
                    error_message="MarkItDown produced empty output",
                )

            # Post-process based on target format
            if target_format == "txt":
                import re
                content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
                content = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", content)
                content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
            elif target_format == "json":
                import json
                content = json.dumps({"content": content, "source": str(input_path)}, indent=2)

            output_path.write_text(content, encoding="utf-8")
            duration = time.time() - start
            size = output_path.stat().st_size

            logger.info(
                "markitdown: conversion complete in %.2fs (%d bytes)",
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
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=f"MarkItDown not installed: {e}. Install: pip install 'markitdown[all]'",
            )

        except Exception as e:
            duration = time.time() - start
            logger.error("markitdown: conversion failed: %s", e, exc_info=True)
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=str(e),
            )
