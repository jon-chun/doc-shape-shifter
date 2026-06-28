import shutil

import pytest

pytest.importorskip("PIL")
pytest.importorskip("pytesseract")
pymupdf = pytest.importorskip("pymupdf")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from doc_shape_shifter.backends.base import ConversionOptions  # noqa: E402
from doc_shape_shifter.converter import convert  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None, reason="tesseract binary not installed"
)

_PHRASE = "The quick brown fox jumps"


def _font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _make_capture(path, repeats=1, width=1000):
    """Build a screenshot-like PNG with crisp rendered text."""
    line_h = 70
    img = Image.new("RGB", (width, line_h * repeats + 40), "white")
    draw = ImageDraw.Draw(img)
    font = _font(34)
    for i in range(repeats):
        draw.text((30, 20 + i * line_h), f"{_PHRASE} line {i}", fill="black", font=font)
    img.save(path)
    return path


def test_png_to_searchable_pdf(tmp_path):
    src = _make_capture(tmp_path / "cap.png", repeats=3)
    out = tmp_path / "out.pdf"
    result = convert(src, out, options=ConversionOptions(mode="searchable"))
    assert result.success, result.error_message
    doc = pymupdf.open(out)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    assert "quick brown fox" in text.lower()


def test_png_to_markdown(tmp_path):
    src = _make_capture(tmp_path / "cap.png", repeats=2)
    out = tmp_path / "out.md"
    result = convert(src, out)
    assert result.success, result.error_message
    content = out.read_text(encoding="utf-8")
    assert content.startswith("# cap")
    assert "quick brown fox" in content.lower()


def test_png_to_text(tmp_path):
    src = _make_capture(tmp_path / "cap.png", repeats=2)
    out = tmp_path / "out.txt"
    result = convert(src, out)
    assert result.success, result.error_message
    assert "quick brown fox" in out.read_text(encoding="utf-8").lower()


def test_png_to_reflow_pdf(tmp_path):
    src = _make_capture(tmp_path / "cap.png", repeats=2)
    out = tmp_path / "reflow.pdf"
    result = convert(src, out, options=ConversionOptions(mode="reflow"))
    assert result.success, result.error_message
    doc = pymupdf.open(out)
    assert doc.page_count >= 1
    text = "".join(p.get_text() for p in doc)
    doc.close()
    assert "quick brown fox" in text.lower()


def test_tall_capture_paginates(tmp_path):
    # ~80 lines of text -> taller than one Letter page once tiled.
    src = _make_capture(tmp_path / "tall.png", repeats=80)
    out = tmp_path / "tall.pdf"
    result = convert(src, out, options=ConversionOptions(mode="searchable"))
    assert result.success, result.error_message
    doc = pymupdf.open(out)
    page_count = doc.page_count
    doc.close()
    assert page_count > 1
