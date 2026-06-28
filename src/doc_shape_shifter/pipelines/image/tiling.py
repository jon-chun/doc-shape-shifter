"""Slice a tall raster image into standard page-sized tiles for OCR + PDF assembly."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

logger = logging.getLogger("doc_shape_shifter.pipelines.image.tiling")

# Portrait page sizes in points (1pt = 1/72 inch).
PAGE_SIZES_PT: dict[str, tuple[float, float]] = {
    "letter": (612.0, 792.0),
    "a4": (595.0, 842.0),
}

# Generous safety cap so genuine GoFullPage captures load but absurd inputs fail loudly.
MAX_IMAGE_PIXELS = 500_000_000


@dataclass
class Tile:
    """One page-sized slice of the source image."""

    index: int
    image: PILImage


def page_px(page_size: str, dpi: int) -> tuple[int, int]:
    """Return (width_px, height_px) for a named page size at a given DPI."""
    if page_size not in PAGE_SIZES_PT:
        raise ValueError(
            f"Unknown page size: {page_size!r}. Use 'letter', 'a4', or 'continuous'."
        )
    w_pt, h_pt = PAGE_SIZES_PT[page_size]
    return round(w_pt / 72 * dpi), round(h_pt / 72 * dpi)


def slice_image(input_path: Path, page_size: str = "letter", dpi: int = 200) -> list[Tile]:
    """Load an image and slice it into page-height tiles.

    For "continuous", the whole image is returned as a single tile. Otherwise the
    image is scaled to the page width and cut into non-overlapping page-height tiles
    (the last tile may be shorter).
    """
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
    img = Image.open(input_path)
    img.load()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    if page_size == "continuous":
        logger.debug("tiling: continuous mode, 1 tile (%dx%d)", img.width, img.height)
        return [Tile(index=0, image=img)]

    page_w_px, page_h_px = page_px(page_size, dpi)
    scale = page_w_px / img.width
    scaled_h = max(1, round(img.height * scale))
    img = img.resize((page_w_px, scaled_h), Image.LANCZOS)

    n = (scaled_h + page_h_px - 1) // page_h_px  # ceil division
    tiles: list[Tile] = []
    for i in range(n):
        top = i * page_h_px
        bottom = min(scaled_h, top + page_h_px)
        tiles.append(Tile(index=i, image=img.crop((0, top, page_w_px, bottom))))

    logger.debug(
        "tiling: %s -> %d tiles (page %dx%d px, dpi=%d)",
        input_path.name, len(tiles), page_w_px, page_h_px, dpi,
    )
    return tiles
