"""Assemble OCR results into PDFs using PyMuPDF (already a core dependency)."""

from __future__ import annotations

import html as html_mod
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

    from .engines.base import OCRPage

logger = logging.getLogger("doc_shape_shifter.pipelines.ocr.assemble")

PAGE_SIZES_PT: dict[str, tuple[float, float]] = {
    "letter": (612.0, 792.0),
    "a4": (595.0, 842.0),
}
_MARGIN_PT = 54.0  # 0.75 inch


def merge_pdf_pages(pdf_blobs: list[bytes], output_path: Path) -> None:
    """Merge a list of single/multi-page PDF byte blobs into one PDF file."""
    import pymupdf

    out = pymupdf.open()
    try:
        for blob in pdf_blobs:
            src = pymupdf.open(stream=blob, filetype="pdf")
            try:
                out.insert_pdf(src)
            finally:
                src.close()
        out.save(str(output_path))
    finally:
        out.close()


def render_text_pdf(text: str, output_path: Path, page_size: str = "letter") -> None:
    """Render plain text into a clean, auto-paginated PDF (reflow mode).

    Uses PyMuPDF's Story API, which flows content across as many pages as needed.
    Line breaks are preserved; blank lines start new paragraphs.
    """
    import pymupdf

    w, h = PAGE_SIZES_PT.get(page_size, PAGE_SIZES_PT["letter"])

    paragraphs = text.split("\n\n")
    body = "".join(
        "<p>" + html_mod.escape(p).replace("\n", "<br/>") + "</p>"
        for p in paragraphs
        if p.strip()
    ) or "<p></p>"
    doc_html = (
        "<html><body style='font-family:sans-serif;font-size:11px;"
        f"line-height:1.4'>{body}</body></html>"
    )

    story = pymupdf.Story(html=doc_html)
    writer = pymupdf.DocumentWriter(str(output_path))
    mediabox = pymupdf.Rect(0, 0, w, h)
    where = pymupdf.Rect(_MARGIN_PT, _MARGIN_PT, w - _MARGIN_PT, h - _MARGIN_PT)

    more = 1
    try:
        while more:
            dev = writer.begin_page(mediabox)
            more, _ = story.place(where)
            story.draw(dev)
            writer.end_page()
    finally:
        writer.close()


def sandwich_page_pdf(tile: PILImage, ocr_page: OCRPage) -> bytes:
    """Build a one-page searchable PDF: the tile image + an invisible OCR text layer.

    Used as the generic searchable-PDF path for engines that return word boxes
    (e.g. Surya). Tesseract overrides this with its native sandwich output.
    """
    import pymupdf

    w, h = float(tile.width), float(tile.height)
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=w, height=h)

        buf = io.BytesIO()
        tile.save(buf, format="PNG")
        page.insert_image(pymupdf.Rect(0, 0, w, h), stream=buf.getvalue())

        for word in ocr_page.words:
            if not word.text.strip():
                continue
            x0, y0, x1, y1 = word.bbox
            fontsize = max(1.0, (y1 - y0) * 0.8)
            # render_mode=3 => invisible (selectable) text.
            page.insert_text(
                (x0, y1), word.text, fontsize=fontsize, render_mode=3, fontname="helv"
            )
        return doc.tobytes()
    finally:
        doc.close()
