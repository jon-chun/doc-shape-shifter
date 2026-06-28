"""OCR engine interface and shared data structures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage


@dataclass
class OCRWord:
    """A recognized text segment with its pixel bounding box (x0, y0, x1, y1)."""

    text: str
    bbox: tuple[float, float, float, float]


@dataclass
class OCRPage:
    """OCR result for a single tile: full text plus optional positioned words."""

    text: str
    words: list[OCRWord] = field(default_factory=list)


class OCREngine(ABC):
    """Abstract pluggable OCR engine."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """True if this engine's dependencies (and binaries) are installed."""

    @abstractmethod
    def recognize(self, tile: PILImage, lang: str = "eng") -> OCRPage:
        """Recognize text in a single tile image."""

    def tile_to_pdf(self, tile: PILImage, lang: str = "eng") -> bytes:
        """Return a one-page searchable PDF (image + invisible text) for the tile.

        Default builds a sandwich from recognize() word boxes; engines with a
        native searchable-PDF output (Tesseract) override this.
        """
        from ..assemble import sandwich_page_pdf

        page = self.recognize(tile, lang)
        return sandwich_page_pdf(tile, page)

    def version_info(self) -> str:
        return self.name
