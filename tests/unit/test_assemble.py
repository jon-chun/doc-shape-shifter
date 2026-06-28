import pytest

pymupdf = pytest.importorskip("pymupdf")

from doc_shape_shifter.pipelines.ocr.assemble import (  # noqa: E402
    merge_pdf_pages,
    render_text_pdf,
)


def _one_page_pdf_bytes(text="page"):
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=200, height=200)
        page.insert_text((20, 40), text)
        return doc.tobytes()
    finally:
        doc.close()


def test_merge_pdf_pages_concatenates(tmp_path):
    out = tmp_path / "merged.pdf"
    merge_pdf_pages([_one_page_pdf_bytes("a"), _one_page_pdf_bytes("b")], out)
    doc = pymupdf.open(out)
    assert doc.page_count == 2
    doc.close()


def test_render_text_pdf_produces_readable_text(tmp_path):
    out = tmp_path / "reflow.pdf"
    render_text_pdf("Hello OCR world.\n\nSecond paragraph.", out, page_size="letter")
    doc = pymupdf.open(out)
    assert doc.page_count >= 1
    extracted = "".join(p.get_text() for p in doc)
    doc.close()
    assert "Hello OCR world" in extracted


def test_render_text_pdf_paginates_long_text(tmp_path):
    out = tmp_path / "long.pdf"
    render_text_pdf("paragraph.\n\n" * 400, out, page_size="letter")
    doc = pymupdf.open(out)
    assert doc.page_count > 1
    doc.close()


def test_merge_pdf_pages_raises_on_invalid_blob(tmp_path):
    # pymupdf raises FileDataError when the stream is not a valid PDF.
    with pytest.raises(pymupdf.FileDataError):
        merge_pdf_pages([b"not a pdf at all"], tmp_path / "bad.pdf")


def test_sandwich_page_pdf_embeds_image_and_text(tmp_path):
    from PIL import Image

    from doc_shape_shifter.pipelines.ocr.assemble import sandwich_page_pdf
    from doc_shape_shifter.pipelines.ocr.engines.base import OCRPage, OCRWord

    tile = Image.new("RGB", (200, 80), "white")
    page = OCRPage(
        text="hello world",
        words=[
            OCRWord(text="hello", bbox=(10, 10, 60, 40)),
            OCRWord(text="world", bbox=(70, 10, 120, 40)),
        ],
    )
    blob = sandwich_page_pdf(tile, page)
    doc = pymupdf.open(stream=blob, filetype="pdf")
    try:
        assert doc.page_count == 1
        text = doc[0].get_text()
    finally:
        doc.close()
    assert "hello" in text and "world" in text
