import pytest

pymupdf = pytest.importorskip("pymupdf")

from doc_shape_shifter.pipelines.ocr.assemble import (  # noqa: E402
    merge_pdf_pages,
    render_text_pdf,
)


def _one_page_pdf_bytes(text="page"):
    doc = pymupdf.open()
    page = doc.new_page(width=200, height=200)
    page.insert_text((20, 40), text)
    blob = doc.tobytes()
    doc.close()
    return blob


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
