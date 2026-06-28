"""Tesseract OCR engine adapter (default, local, lightweight)."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING

from .base import OCREngine, OCRPage

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

logger = logging.getLogger("doc_shape_shifter.pipelines.ocr.engines.tesseract")


class TesseractEngine(OCREngine):
    """OCR via the `tesseract` binary through pytesseract."""

    name = "tesseract"

    def is_available(self) -> bool:
        if shutil.which("tesseract") is None:
            logger.debug("tesseract binary not found on PATH")
            return False
        try:
            import pytesseract  # noqa: F401
            return True
        except ImportError:
            logger.debug("pytesseract not installed")
            return False

    def version_info(self) -> str:
        try:
            import pytesseract
            return f"tesseract {pytesseract.get_tesseract_version()}"
        except Exception:
            return "tesseract (not available)"

    def recognize(self, tile: PILImage, lang: str = "eng") -> OCRPage:
        import pytesseract

        text = pytesseract.image_to_string(tile, lang=lang)
        return OCRPage(text=text)

    def tile_to_pdf(self, tile: PILImage, lang: str = "eng") -> bytes:
        import pytesseract

        # Native sandwich PDF: original image + invisible OCR text layer.
        return pytesseract.image_to_pdf_or_hocr(tile, lang=lang, extension="pdf")
