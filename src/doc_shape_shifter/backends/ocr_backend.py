"""OCR backend — image (PNG/JPG/...) -> searchable/reflow PDF, Markdown, or text."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from .base import BaseBackend, ConversionOptions, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.ocr")

_SUPPORTED_TARGETS = ("pdf", "md", "txt")


class OCRBackend(BaseBackend):
    """Convert images to text-bearing outputs via a pluggable OCR engine."""

    name = "ocr"

    def is_available(self) -> bool:
        # Available if the DEFAULT engine (tesseract) is usable. Opt-in engines
        # (surya) are validated per-conversion from options.
        from ..pipelines.ocr.engines import get_engine

        try:
            return get_engine("tesseract").is_available()
        except Exception:
            return False

    def version_info(self) -> str:
        from ..pipelines.ocr.engines import get_engine

        try:
            return f"ocr ({get_engine('tesseract').version_info()})"
        except Exception:
            return "ocr (no engine available)"

    def _fail(self, msg: str, start: float, src: str, tgt: str) -> ConversionResult:
        return ConversionResult(
            success=False, output_path=None, backend_name=self.name,
            duration_seconds=time.time() - start,
            source_format=src, target_format=tgt, error_message=msg,
        )

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
        options: ConversionOptions | None = None,
    ) -> ConversionResult:
        start = time.time()
        opts = options or ConversionOptions()
        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info(
            "ocr: %s -> %s (%s, engine=%s, mode=%s)",
            source_format, target_format, input_path.name, opts.ocr_engine, opts.mode,
        )

        if target_format not in _SUPPORTED_TARGETS:
            return self._fail(
                f"OCR backend outputs pdf/md/txt, not {target_format}",
                start, source_format, target_format,
            )

        from ..pipelines.image.tiling import slice_image
        from ..pipelines.ocr.assemble import merge_pdf_pages, render_text_pdf
        from ..pipelines.ocr.engines import get_engine

        try:
            engine = get_engine(opts.ocr_engine)
        except ValueError as e:
            return self._fail(str(e), start, source_format, target_format)

        if not engine.is_available():
            hint = (
                "install tesseract-ocr + pip install 'doc-shape-shifter[ocr]'"
                if opts.ocr_engine == "tesseract"
                else "pip install 'doc-shape-shifter[ocr-ml]'"
            )
            return self._fail(
                f"OCR engine '{opts.ocr_engine}' not available ({hint})",
                start, source_format, target_format,
            )

        try:
            tiles = slice_image(input_path, opts.page_size, opts.dpi)
            warnings: list[str] = []

            if target_format == "pdf" and opts.mode == "searchable":
                blobs = [engine.tile_to_pdf(t.image, opts.ocr_lang) for t in tiles]
                merge_pdf_pages(blobs, output_path)
            else:
                parts = [engine.recognize(t.image, opts.ocr_lang).text.strip() for t in tiles]
                text = "\n\n".join(p for p in parts if p).strip()
                if not text:
                    warnings.append("OCR produced no text — image may be blank or unreadable.")

                if target_format == "pdf":  # reflow
                    pg = opts.page_size if opts.page_size in ("letter", "a4") else "letter"
                    render_text_pdf(text, output_path, page_size=pg)
                elif target_format == "md":
                    output_path.write_text(f"# {input_path.stem}\n\n{text}\n", encoding="utf-8")
                else:  # txt
                    output_path.write_text(text + "\n", encoding="utf-8")

            duration = time.time() - start
            size = output_path.stat().st_size
            logger.info("ocr: complete in %.2fs (%d bytes, %d tiles)", duration, size, len(tiles))
            return ConversionResult(
                success=True, output_path=output_path, backend_name=self.name,
                duration_seconds=duration, source_format=source_format,
                target_format=target_format, file_size_bytes=size, warnings=warnings,
            )
        except Exception as e:
            logger.error("ocr: conversion failed: %s", e, exc_info=True)
            return self._fail(str(e), start, source_format, target_format)
