import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from doc_shape_shifter.pipelines.image.tiling import slice_image  # noqa: E402


def _make_png(tmp_path, width, height):
    p = tmp_path / "tall.png"
    Image.new("RGB", (width, height), "white").save(p)
    return p


def test_slice_exact_three_pages(tmp_path):
    # letter @200dpi -> page is 1700x2200 px. Width already 1700 => scale 1.0.
    p = _make_png(tmp_path, 1700, 6600)  # 3 * 2200
    tiles = slice_image(p, page_size="letter", dpi=200)
    assert len(tiles) == 3
    assert tiles[0].image.width == 1700
    assert tiles[0].image.height == 2200


def test_slice_rounds_up_partial_page(tmp_path):
    p = _make_png(tmp_path, 1700, 6601)  # one pixel into a 4th page
    tiles = slice_image(p, page_size="letter", dpi=200)
    assert len(tiles) == 4
    assert tiles[-1].image.height == 1  # remainder


def test_slice_scales_to_page_width(tmp_path):
    p = _make_png(tmp_path, 850, 4400)  # half width -> scale 2.0 -> 8800 tall
    tiles = slice_image(p, page_size="letter", dpi=200)
    assert tiles[0].image.width == 1700
    assert len(tiles) == 4  # ceil(8800 / 2200)


def test_continuous_is_single_tile(tmp_path):
    p = _make_png(tmp_path, 800, 9000)
    tiles = slice_image(p, page_size="continuous", dpi=200)
    assert len(tiles) == 1
    assert tiles[0].image.height == 9000


def test_unknown_page_size_raises(tmp_path):
    p = _make_png(tmp_path, 100, 100)
    with pytest.raises(ValueError):
        slice_image(p, page_size="tabloid", dpi=200)
