"""OCR engine registry."""

from __future__ import annotations

from .base import OCREngine, OCRPage, OCRWord

__all__ = ["OCREngine", "OCRPage", "OCRWord", "get_engine"]


def get_engine(name: str) -> OCREngine:
    """Instantiate an OCR engine by name."""
    if name == "tesseract":
        from .tesseract import TesseractEngine
        return TesseractEngine()
    if name == "surya":
        from .surya import SuryaEngine
        return SuryaEngine()
    raise ValueError(f"Unknown OCR engine: {name!r}. Use 'tesseract' or 'surya'.")
