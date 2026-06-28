"""Surya OCR engine adapter (opt-in, ML-based, higher accuracy)."""

from __future__ import annotations

import importlib.util
import logging
from typing import TYPE_CHECKING

from .base import OCREngine, OCRPage, OCRWord

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

logger = logging.getLogger("doc_shape_shifter.pipelines.ocr.engines.surya")


class SuryaEngine(OCREngine):
    """OCR via Surya predictors. Returns line-level text + boxes for sandwiching."""

    name = "surya"

    def __init__(self) -> None:
        self._rec = None
        self._det = None

    def is_available(self) -> bool:
        return importlib.util.find_spec("surya") is not None

    def version_info(self) -> str:
        if not self.is_available():
            return "surya (not installed)"
        try:
            import surya
            return f"surya {getattr(surya, '__version__', 'unknown')}"
        except Exception:
            return "surya (unknown version)"

    def _load(self) -> None:
        if self._rec is not None:
            return
        from surya.detection import DetectionPredictor
        from surya.recognition import RecognitionPredictor

        self._det = DetectionPredictor()
        self._rec = RecognitionPredictor()

    def recognize(self, tile: PILImage, lang: str = "eng") -> OCRPage:
        self._load()
        langs = [seg for seg in lang.replace("+", ",").split(",") if seg]
        predictions = self._rec([tile], [langs], self._det)
        result = predictions[0]

        words: list[OCRWord] = []
        lines_text: list[str] = []
        for line in getattr(result, "text_lines", []):
            text = getattr(line, "text", "") or ""
            bbox = getattr(line, "bbox", None)
            lines_text.append(text)
            if bbox and len(bbox) == 4:
                words.append(OCRWord(text=text, bbox=tuple(float(v) for v in bbox)))
        return OCRPage(text="\n".join(lines_text), words=words)
