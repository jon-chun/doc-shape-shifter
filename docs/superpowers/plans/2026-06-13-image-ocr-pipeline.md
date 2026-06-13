# Image OCR Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let doc-shape-shifter convert raster images (esp. tall GoFullPage `*.png` captures) into a searchable text-layer PDF, a reflowed text PDF, Markdown, or plain text via a pluggable OCR pipeline (Tesseract default, Surya opt-in).

**Architecture:** Approach C (hybrid). A single `IMAGE` `DocFormat` flows through the existing detect→route→convert→fallback machinery to a new `OCRBackend`. The backend slices the tall image into Letter/A4 page tiles (`pipelines/image/tiling.py`), runs a pluggable `OCREngine` (`pipelines/ocr/engines/`), and assembles output with PyMuPDF (`pipelines/ocr/assemble.py`) — no new PDF-rendering dependency. OCR-specific knobs travel via a new `ConversionOptions` dataclass added to the backend interface.

**Tech Stack:** Python 3.10+, Pillow, pytesseract + system `tesseract-ocr`, PyMuPDF (existing core dep), surya-ocr (opt-in), click, pytest.

**Branch:** `feature/image-ocr-pipeline` (already checked out).

**Conventions:** Heavy libs imported *inside* methods (matches existing backends). Every backend method returns `ConversionResult`. Run `uv run pytest` / `uv run ruff check src/ tests/` per project CLAUDE.md.

---

### Task 1: Add `IMAGE` format + extension/MIME maps

**Files:**
- Modify: `src/doc_shape_shifter/utils/formats.py`
- Test: `tests/unit/test_formats.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_formats.py`:

```python
from doc_shape_shifter.utils.formats import (
    EXTENSION_MAP,
    FORMAT_EXTENSION,
    MIME_MAP,
    DocFormat,
    format_from_string,
)


def test_image_format_exists():
    assert DocFormat.IMAGE.value == "image"


def test_image_extensions_map_to_image():
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"):
        assert EXTENSION_MAP[ext] == DocFormat.IMAGE


def test_image_mimes_map_to_image():
    for mime in ("image/png", "image/jpeg", "image/webp", "image/tiff", "image/bmp"):
        assert MIME_MAP[mime] == DocFormat.IMAGE


def test_image_not_an_output_format():
    # IMAGE is only ever a source; it must not be a default output target.
    assert DocFormat.IMAGE not in FORMAT_EXTENSION


def test_format_from_string_image():
    assert format_from_string("image") == DocFormat.IMAGE
    assert format_from_string("png") == DocFormat.IMAGE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_formats.py -k image -v`
Expected: FAIL with `AttributeError: IMAGE` / `KeyError`.

- [ ] **Step 3: Add the IMAGE member and map entries**

In `src/doc_shape_shifter/utils/formats.py`, add to the `DocFormat` enum (after `RTF = "rtf"`):

```python
    RTF = "rtf"
    IMAGE = "image"
```

Add these entries to `EXTENSION_MAP` (after the `.rtf` line):

```python
    ".png": DocFormat.IMAGE,
    ".jpg": DocFormat.IMAGE,
    ".jpeg": DocFormat.IMAGE,
    ".webp": DocFormat.IMAGE,
    ".tif": DocFormat.IMAGE,
    ".tiff": DocFormat.IMAGE,
    ".bmp": DocFormat.IMAGE,
```

Add these entries to `MIME_MAP` (after the rtf lines):

```python
    "image/png": DocFormat.IMAGE,
    "image/jpeg": DocFormat.IMAGE,
    "image/webp": DocFormat.IMAGE,
    "image/tiff": DocFormat.IMAGE,
    "image/bmp": DocFormat.IMAGE,
    "image/x-ms-bmp": DocFormat.IMAGE,
```

Do **not** add `IMAGE` to `FORMAT_EXTENSION` or `PANDOC_FORMAT_MAP` (it is never an output and not a pandoc format).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_formats.py -v`
Expected: PASS (new tests + existing tests).

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/utils/formats.py tests/unit/test_formats.py
git commit -m "feat(formats): add IMAGE format with png/jpg/webp/tiff/bmp mappings"
```

---

### Task 2: Image detection via magic bytes

**Files:**
- Modify: `src/doc_shape_shifter/detector.py`
- Test: `tests/unit/test_detector.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_detector.py`:

```python
from doc_shape_shifter.detector import _detect_by_heuristic, detect_format
from doc_shape_shifter.utils.formats import DocFormat


def test_heuristic_detects_png(tmp_path):
    p = tmp_path / "capture.bin"  # non-image extension forces heuristic path
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    assert _detect_by_heuristic(p) == DocFormat.IMAGE


def test_heuristic_detects_jpeg(tmp_path):
    p = tmp_path / "capture.bin"
    p.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)
    assert _detect_by_heuristic(p) == DocFormat.IMAGE


def test_heuristic_detects_bmp(tmp_path):
    p = tmp_path / "capture.bin"
    p.write_bytes(b"BM" + b"\x00" * 64)
    assert _detect_by_heuristic(p) == DocFormat.IMAGE


def test_heuristic_detects_webp(tmp_path):
    p = tmp_path / "capture.bin"
    p.write_bytes(b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 64)
    assert _detect_by_heuristic(p) == DocFormat.IMAGE


def test_detect_png_by_extension(tmp_path):
    p = tmp_path / "capture.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    assert detect_format(p) == DocFormat.IMAGE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_detector.py -k "png or jpeg or bmp or webp" -v`
Expected: FAIL (`_detect_by_heuristic` returns None for image bytes).

- [ ] **Step 3: Add image magic-byte checks**

In `src/doc_shape_shifter/detector.py`, inside `_detect_by_heuristic`, immediately after the line `header = f.read(4096)` block and **before** the `%PDF-` check, add:

```python
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            logger.debug("Heuristic: PNG header detected")
            return DocFormat.IMAGE

        if header[:3] == b"\xff\xd8\xff":
            logger.debug("Heuristic: JPEG header detected")
            return DocFormat.IMAGE

        if header[:2] == b"BM":
            logger.debug("Heuristic: BMP header detected")
            return DocFormat.IMAGE

        if header[:4] in (b"II*\x00", b"MM\x00*"):
            logger.debug("Heuristic: TIFF header detected")
            return DocFormat.IMAGE

        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            logger.debug("Heuristic: WEBP header detected")
            return DocFormat.IMAGE
```

(The `%PDF-` and ZIP checks remain below these.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_detector.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/detector.py tests/unit/test_detector.py
git commit -m "feat(detector): detect png/jpeg/bmp/tiff/webp via magic bytes"
```

---

### Task 3: `ConversionOptions` + thread options through the backend interface

**Files:**
- Modify: `src/doc_shape_shifter/backends/base.py`
- Modify: `src/doc_shape_shifter/converter.py`
- Modify (signature only, accept-and-ignore): `builtin_backend.py`, `pymupdf_backend.py`, `pandoc_backend.py`, `docling_backend.py`, `markitdown_backend.py`, `tabula_backend.py`, `mathpix_backend.py`
- Test: `tests/unit/test_backends.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_backends.py`:

```python
from pathlib import Path

from doc_shape_shifter.backends.base import ConversionOptions
from doc_shape_shifter.backends.builtin_backend import BuiltinBackend


def test_conversion_options_defaults():
    o = ConversionOptions()
    assert o.mode == "searchable"
    assert o.ocr_engine == "tesseract"
    assert o.page_size == "letter"
    assert o.dpi == 200
    assert o.ocr_lang == "eng"


def test_existing_backend_accepts_options_kwarg(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("# Title\n\nhello", encoding="utf-8")
    out = tmp_path / "a.txt"
    be = BuiltinBackend()
    # Passing options must not raise and must still work.
    result = be.convert(src, out, "md", "txt", options=ConversionOptions())
    assert result.success
    assert out.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_backends.py -k options -v`
Expected: FAIL (`ImportError: ConversionOptions` and/or `TypeError: unexpected keyword 'options'`).

- [ ] **Step 3a: Add `ConversionOptions` and extend the ABC**

In `src/doc_shape_shifter/backends/base.py`, add this dataclass after the `ConversionResult` class:

```python
@dataclass
class ConversionOptions:
    """Optional, backend-specific knobs threaded from CLI/API to a backend.

    Only the OCR backend reads these today; other backends accept and ignore them.
    """

    mode: str = "searchable"        # "searchable" | "reflow" (image -> pdf)
    ocr_engine: str = "tesseract"   # "tesseract" | "surya"
    page_size: str = "letter"       # "letter" | "a4" | "continuous"
    dpi: int = 200
    ocr_lang: str = "eng"           # e.g. "eng" or "eng+fra"
```

Change the abstract `convert` signature in `BaseBackend` to:

```python
    @abstractmethod
    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
        options: "ConversionOptions | None" = None,
    ) -> ConversionResult:
        """Execute a format conversion."""
```

- [ ] **Step 3b: Add the `options` param to all 7 existing backends**

In each of `builtin_backend.py`, `pymupdf_backend.py`, `pandoc_backend.py`, `docling_backend.py`, `markitdown_backend.py`, `tabula_backend.py`, `mathpix_backend.py`, change the `def convert(` signature by adding the new last parameter. The body is unchanged. Example for `builtin_backend.py` (line ~57):

```python
    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
        options=None,
    ) -> ConversionResult:
```

Apply the identical `options=None,` addition to the other six backends' `convert` signatures.

- [ ] **Step 3c: Thread `options` through the orchestrator**

In `src/doc_shape_shifter/converter.py`:

Add the import near the top (with the other backends import):

```python
from .backends.base import ConversionOptions, ConversionResult
```

Add `options` to the `convert()` signature (after `show_progress`):

```python
def convert(
    input_path: str | Path,
    output_path: str | Path | None = None,
    target_format: str | None = None,
    backend: str | None = None,
    fallback: bool = True,
    show_progress: bool = False,
    options: ConversionOptions | None = None,
) -> ConversionResult:
```

In the call to `_run_with_progress` (around line 129), add `options=options`:

```python
        result = _run_with_progress(
            be,
            input_path,
            output_path,
            source_fmt.value,
            target_fmt.value,
            eta_seconds=eta,
            show_progress=show_progress,
            options=options,
        )
```

Update `_run_with_progress` to accept and forward `options`:

```python
def _run_with_progress(
    be, input_path, output_path, src_fmt, tgt_fmt, eta_seconds, show_progress, options=None
):
    """Run a backend conversion, optionally wrapped in a progress bar."""
    if show_progress:
        from .utils.progress import ConversionProgress

        desc = f"{src_fmt} -> {tgt_fmt}"
        with ConversionProgress(desc, be.name, eta_seconds=eta_seconds):
            return be.convert(input_path, output_path, src_fmt, tgt_fmt, options=options)
    else:
        return be.convert(input_path, output_path, src_fmt, tgt_fmt, options=options)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/ -v`
Expected: PASS (new options tests + all existing unit tests unaffected).

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/backends/ src/doc_shape_shifter/converter.py tests/unit/test_backends.py
git commit -m "feat(core): add ConversionOptions and thread options through backends"
```

---

### Task 4: Router matrix entries for image sources

**Files:**
- Modify: `src/doc_shape_shifter/router.py`
- Test: `tests/unit/test_router.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_router.py`:

```python
import pytest

from doc_shape_shifter.router import (
    UnsupportedConversionError,
    get_backend_chain,
)
from doc_shape_shifter.utils.formats import DocFormat


def test_image_to_pdf_routes_to_ocr():
    assert get_backend_chain(DocFormat.IMAGE, DocFormat.PDF) == ["ocr"]


def test_image_to_markdown_routes_to_ocr():
    assert get_backend_chain(DocFormat.IMAGE, DocFormat.MARKDOWN) == ["ocr"]


def test_image_to_text_routes_to_ocr():
    assert get_backend_chain(DocFormat.IMAGE, DocFormat.PLAIN_TEXT) == ["ocr"]


def test_image_to_docx_unsupported():
    with pytest.raises(UnsupportedConversionError):
        get_backend_chain(DocFormat.IMAGE, DocFormat.DOCX)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_router.py -k image -v`
Expected: FAIL with `UnsupportedConversionError` on the first three.

- [ ] **Step 3: Add matrix entries**

In `src/doc_shape_shifter/router.py`, add a new section to `CONVERSION_MATRIX` (after the `# --- RTF as source ---` block, before the closing `}`):

```python
    # --- Image as source (OCR) ---
    (DocFormat.IMAGE, DocFormat.PDF):        ["ocr"],
    (DocFormat.IMAGE, DocFormat.MARKDOWN):   ["ocr"],
    (DocFormat.IMAGE, DocFormat.PLAIN_TEXT): ["ocr"],
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_router.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/router.py tests/unit/test_router.py
git commit -m "feat(router): route image -> pdf/md/txt through the ocr backend"
```

---

### Task 5: Image tiling pipeline

**Files:**
- Create: `src/doc_shape_shifter/pipelines/image/tiling.py`
- Test: `tests/unit/test_tiling.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_tiling.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_tiling.py -v`
Expected: FAIL (`ModuleNotFoundError: ...pipelines.image.tiling`).

- [ ] **Step 3: Implement tiling**

Create `src/doc_shape_shifter/pipelines/image/tiling.py`:

```python
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
    image: "PILImage"


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_tiling.py -v`
Expected: PASS (requires Pillow: `uv pip install -e ".[ocr]"` if it skips).

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/pipelines/image/tiling.py tests/unit/test_tiling.py
git commit -m "feat(pipelines): add page-aware image tiling for tall captures"
```

---

### Task 6: PDF assembly (merge, reflow render, sandwich page)

**Files:**
- Create: `src/doc_shape_shifter/pipelines/ocr/assemble.py`
- Test: `tests/unit/test_assemble.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_assemble.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_assemble.py -v`
Expected: FAIL (`ModuleNotFoundError: ...pipelines.ocr.assemble`).

- [ ] **Step 3: Implement assembly**

Create `src/doc_shape_shifter/pipelines/ocr/assemble.py`:

```python
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
            out.insert_pdf(src)
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

    paragraphs = [p for p in text.split("\n\n")]
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
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()


def sandwich_page_pdf(tile: "PILImage", ocr_page: "OCRPage") -> bytes:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_assemble.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/pipelines/ocr/assemble.py tests/unit/test_assemble.py
git commit -m "feat(pipelines): PDF assembly (merge, reflow render, sandwich page)"
```

---

### Task 7: OCR engine interface + Tesseract adapter + engine factory

**Files:**
- Create: `src/doc_shape_shifter/pipelines/ocr/engines/base.py`
- Create: `src/doc_shape_shifter/pipelines/ocr/engines/tesseract.py`
- Create: `src/doc_shape_shifter/pipelines/ocr/engines/__init__.py`
- Test: `tests/unit/test_ocr_engines.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_ocr_engines.py`:

```python
from doc_shape_shifter.pipelines.ocr.engines import get_engine
from doc_shape_shifter.pipelines.ocr.engines.base import OCRPage, OCRWord
from doc_shape_shifter.pipelines.ocr.engines.tesseract import TesseractEngine


def test_get_engine_returns_tesseract():
    assert isinstance(get_engine("tesseract"), TesseractEngine)


def test_get_engine_unknown_raises():
    import pytest

    with pytest.raises(ValueError):
        get_engine("nope")


def test_ocr_dataclasses():
    page = OCRPage(text="hi", words=[OCRWord(text="hi", bbox=(0, 0, 1, 1))])
    assert page.text == "hi"
    assert page.words[0].bbox == (0, 0, 1, 1)


def test_tesseract_availability_requires_binary(monkeypatch):
    import doc_shape_shifter.pipelines.ocr.engines.tesseract as mod

    monkeypatch.setattr(mod.shutil, "which", lambda _: None)
    assert TesseractEngine().is_available() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_ocr_engines.py -v`
Expected: FAIL (`ModuleNotFoundError: ...engines`).

- [ ] **Step 3a: Create the engine ABC**

Create `src/doc_shape_shifter/pipelines/ocr/engines/base.py`:

```python
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
    def recognize(self, tile: "PILImage", lang: str = "eng") -> OCRPage:
        """Recognize text in a single tile image."""

    def tile_to_pdf(self, tile: "PILImage", lang: str = "eng") -> bytes:
        """Return a one-page searchable PDF (image + invisible text) for the tile.

        Default builds a sandwich from recognize() word boxes; engines with a
        native searchable-PDF output (Tesseract) override this.
        """
        from ..assemble import sandwich_page_pdf

        page = self.recognize(tile, lang)
        return sandwich_page_pdf(tile, page)

    def version_info(self) -> str:
        return self.name
```

- [ ] **Step 3b: Create the Tesseract adapter**

Create `src/doc_shape_shifter/pipelines/ocr/engines/tesseract.py`:

```python
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

    def recognize(self, tile: "PILImage", lang: str = "eng") -> OCRPage:
        import pytesseract

        text = pytesseract.image_to_string(tile, lang=lang)
        return OCRPage(text=text)

    def tile_to_pdf(self, tile: "PILImage", lang: str = "eng") -> bytes:
        import pytesseract

        # Native sandwich PDF: original image + invisible OCR text layer.
        return pytesseract.image_to_pdf_or_hocr(tile, lang=lang, extension="pdf")
```

- [ ] **Step 3c: Create the engine factory**

Create `src/doc_shape_shifter/pipelines/ocr/engines/__init__.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_ocr_engines.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/pipelines/ocr/engines/ tests/unit/test_ocr_engines.py
git commit -m "feat(pipelines): OCR engine interface + Tesseract adapter + factory"
```

---

### Task 8: OCRBackend wiring + registration + estimator entries

**Files:**
- Create: `src/doc_shape_shifter/backends/ocr_backend.py`
- Modify: `src/doc_shape_shifter/backends/__init__.py`
- Modify: `src/doc_shape_shifter/utils/estimator.py`
- Test: `tests/unit/test_backends.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_backends.py`:

```python
from doc_shape_shifter.backends import get_backend, list_backends
from doc_shape_shifter.backends.ocr_backend import OCRBackend


def test_ocr_backend_registered():
    names = [name for name, _ in list_backends()]
    assert "ocr" in names
    assert isinstance(get_backend("ocr"), OCRBackend)


def test_ocr_backend_rejects_unsupported_target(tmp_path):
    img = tmp_path / "x.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    be = OCRBackend()
    result = be.convert(img, tmp_path / "x.docx", "image", "docx")
    assert result.success is False
    assert "docx" in (result.error_message or "")


def test_ocr_backend_unknown_engine_fails(tmp_path):
    from doc_shape_shifter.backends.base import ConversionOptions

    img = tmp_path / "x.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    be = OCRBackend()
    result = be.convert(
        img, tmp_path / "x.txt", "image", "txt",
        options=ConversionOptions(ocr_engine="bogus"),
    )
    assert result.success is False
    assert "bogus" in (result.error_message or "")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_backends.py -k ocr -v`
Expected: FAIL (`ModuleNotFoundError`/`ocr` not registered).

- [ ] **Step 3a: Implement the OCR backend**

Create `src/doc_shape_shifter/backends/ocr_backend.py`:

```python
"""OCR backend — image (PNG/JPG/...) -> searchable/reflow PDF, Markdown, or text."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from .base import BaseBackend, ConversionOptions, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.ocr")

_SUPPORTED_TARGETS = ("pdf", "md", "txt")


class OCRBackend(BaseBackend):
    """Convert images to text-bearing outputs via a pluggable OCR engine."""

    name = "ocr"

    def is_available(self) -> bool:
        # Available if the DEFAULT engine (tesseract) is usable. Opt-in engines
        # (surya) are validated per-conversion from options.
        from ..pipelines.ocr.engines import get_engine

        try:
            return get_engine("tesseract").is_available()
        except Exception:
            return False

    def version_info(self) -> str:
        from ..pipelines.ocr.engines import get_engine

        try:
            return f"ocr ({get_engine('tesseract').version_info()})"
        except Exception:
            return "ocr (no engine available)"

    def _fail(self, msg, start, src, tgt) -> ConversionResult:
        return ConversionResult(
            success=False, output_path=None, backend_name=self.name,
            duration_seconds=time.time() - start,
            source_format=src, target_format=tgt, error_message=msg,
        )

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
        options: ConversionOptions | None = None,
    ) -> ConversionResult:
        start = time.time()
        opts = options or ConversionOptions()
        input_path = Path(input_path)
        output_path = Path(output_path)
        logger.info(
            "ocr: %s -> %s (%s, engine=%s, mode=%s)",
            source_format, target_format, input_path.name, opts.ocr_engine, opts.mode,
        )

        if target_format not in _SUPPORTED_TARGETS:
            return self._fail(
                f"OCR backend outputs pdf/md/txt, not {target_format}",
                start, source_format, target_format,
            )

        from ..pipelines.image.tiling import slice_image
        from ..pipelines.ocr.assemble import merge_pdf_pages, render_text_pdf
        from ..pipelines.ocr.engines import get_engine

        try:
            engine = get_engine(opts.ocr_engine)
        except ValueError as e:
            return self._fail(str(e), start, source_format, target_format)

        if not engine.is_available():
            hint = (
                "install tesseract-ocr + pip install 'doc-shape-shifter[ocr]'"
                if opts.ocr_engine == "tesseract"
                else "pip install 'doc-shape-shifter[ocr-ml]'"
            )
            return self._fail(
                f"OCR engine '{opts.ocr_engine}' not available ({hint})",
                start, source_format, target_format,
            )

        try:
            tiles = slice_image(input_path, opts.page_size, opts.dpi)
            warnings: list[str] = []

            if target_format == "pdf" and opts.mode == "searchable":
                blobs = [engine.tile_to_pdf(t.image, opts.ocr_lang) for t in tiles]
                merge_pdf_pages(blobs, output_path)
            else:
                parts = [engine.recognize(t.image, opts.ocr_lang).text.strip() for t in tiles]
                text = "\n\n".join(p for p in parts if p).strip()
                if not text:
                    warnings.append("OCR produced no text — image may be blank or unreadable.")

                if target_format == "pdf":  # reflow
                    pg = opts.page_size if opts.page_size in ("letter", "a4") else "letter"
                    render_text_pdf(text, output_path, page_size=pg)
                elif target_format == "md":
                    output_path.write_text(f"# {input_path.stem}\n\n{text}\n", encoding="utf-8")
                else:  # txt
                    output_path.write_text(text + "\n", encoding="utf-8")

            duration = time.time() - start
            size = output_path.stat().st_size
            logger.info("ocr: complete in %.2fs (%d bytes, %d tiles)", duration, size, len(tiles))
            return ConversionResult(
                success=True, output_path=output_path, backend_name=self.name,
                duration_seconds=duration, source_format=source_format,
                target_format=target_format, file_size_bytes=size, warnings=warnings,
            )
        except Exception as e:
            logger.error("ocr: conversion failed: %s", e, exc_info=True)
            return self._fail(str(e), start, source_format, target_format)
```

- [ ] **Step 3b: Register the backend**

In `src/doc_shape_shifter/backends/__init__.py`, inside `_register_backends()`:

Add the import (with the other backend imports):

```python
    from .ocr_backend import OCRBackend
```

Add `OCRBackend` to the registration list:

```python
    for cls in [
        BuiltinBackend, PyMuPDFBackend, PandocBackend, DoclingBackend,
        MarkItDownBackend, TabulaBackend, MathpixBackend, OCRBackend,
    ]:
        _BACKEND_CLASSES[cls.name] = cls
```

- [ ] **Step 3c: Add estimator entries for OCR**

In `src/doc_shape_shifter/utils/estimator.py`:

Add to `_BASE_TIMES` (before the closing `}`):

```python
    # ocr — tesseract per-tile OCR, image source
    ("ocr", "image", "pdf"): 4.0,
    ("ocr", "image", "md"): 4.0,
    ("ocr", "image", "txt"): 4.0,
```

Add to `_BACKEND_DEFAULTS`:

```python
    "ocr": 4.0,
```

Add to `_SIZE_SCALE_PER_MB`:

```python
    "ocr": 6.0,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_backends.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/backends/ocr_backend.py src/doc_shape_shifter/backends/__init__.py src/doc_shape_shifter/utils/estimator.py tests/unit/test_backends.py
git commit -m "feat(backends): add OCRBackend, register it, add OCR time estimates"
```

---

### Task 9: Surya engine adapter (opt-in)

**Files:**
- Create: `src/doc_shape_shifter/pipelines/ocr/engines/surya.py`
- Test: `tests/unit/test_ocr_engines.py`

> **Execution note:** Surya's import paths change across releases. The code below
> targets the predictor API (surya-ocr ≥ 0.6 / recent "foundation" releases). If
> `uv run python -c "from surya.recognition import RecognitionPredictor"` fails on
> the installed version, adjust the two imports in `_load()` to match that version's
> module layout, but keep the `recognize()` output mapping identical. The unit test
> below does not require Surya to be installed.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_ocr_engines.py`:

```python
def test_surya_engine_selectable_and_gated():
    from doc_shape_shifter.pipelines.ocr.engines import get_engine
    from doc_shape_shifter.pipelines.ocr.engines.surya import SuryaEngine

    eng = get_engine("surya")
    assert isinstance(eng, SuryaEngine)
    # is_available reflects whether surya is importable; must not raise either way.
    assert isinstance(eng.is_available(), bool)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_ocr_engines.py -k surya -v`
Expected: FAIL (`ModuleNotFoundError: ...engines.surya`).

- [ ] **Step 3: Implement the Surya adapter**

Create `src/doc_shape_shifter/pipelines/ocr/engines/surya.py`:

```python
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

    def recognize(self, tile: "PILImage", lang: str = "eng") -> OCRPage:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_ocr_engines.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/pipelines/ocr/engines/surya.py tests/unit/test_ocr_engines.py
git commit -m "feat(pipelines): add opt-in Surya OCR engine adapter"
```

---

### Task 10: CLI flags for OCR

**Files:**
- Modify: `src/doc_shape_shifter/cli.py`
- Test: `tests/unit/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_cli.py` (or append if it exists):

```python
from click.testing import CliRunner

from doc_shape_shifter.cli import main


def test_help_lists_ocr_flags():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for flag in ("--mode", "--ocr-engine", "--page-size", "--dpi", "--ocr-lang"):
        assert flag in result.output


def test_list_formats_includes_image_pairs():
    result = CliRunner().invoke(main, ["--list-formats"])
    assert result.exit_code == 0
    assert "image" in result.output


def test_invalid_mode_rejected():
    result = CliRunner().invoke(main, ["x.png", "y.pdf", "--mode", "bogus"])
    assert result.exit_code != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_cli.py -v`
Expected: FAIL (flags absent from `--help`).

- [ ] **Step 3: Add CLI options and pass ConversionOptions**

In `src/doc_shape_shifter/cli.py`, add these options after the existing `--no-progress` option decorator (before `--list-backends`):

```python
@click.option("--mode", type=click.Choice(["searchable", "reflow"]),
              default="searchable", show_default=True,
              help="OCR PDF mode for image sources: searchable (image+text layer) or reflow.")
@click.option("--ocr-engine", type=click.Choice(["tesseract", "surya"]),
              default="tesseract", show_default=True,
              help="OCR engine for image sources.")
@click.option("--page-size", type=click.Choice(["letter", "a4", "continuous"]),
              default="letter", show_default=True,
              help="Output page size for OCR PDFs.")
@click.option("--dpi", type=int, default=200, show_default=True,
              help="Rendering DPI used to tile image sources.")
@click.option("--ocr-lang", default="eng", show_default=True,
              help="OCR language(s), e.g. 'eng' or 'eng+fra'.")
```

Add the matching parameters to the `main(...)` function signature (after `no_progress: bool,`):

```python
    mode: str,
    ocr_engine: str,
    page_size: str,
    dpi: int,
    ocr_lang: str,
```

In the conversion section, build options and pass them. Replace the existing
`from .converter import convert` / `result = convert(...)` block with:

```python
    from .backends.base import ConversionOptions
    from .converter import convert

    console.print(f"[bold]Converting:[/] {input_file}", highlight=False)

    options = ConversionOptions(
        mode=mode,
        ocr_engine=ocr_engine,
        page_size=page_size,
        dpi=dpi,
        ocr_lang=ocr_lang,
    )

    result = convert(
        input_path=input_file,
        output_path=output_file,
        target_format=target_format,
        backend=backend,
        fallback=not no_fallback,
        show_progress=not no_progress,
        options=options,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/doc_shape_shifter/cli.py tests/unit/test_cli.py
git commit -m "feat(cli): add --mode/--ocr-engine/--page-size/--dpi/--ocr-lang"
```

---

### Task 11: Packaging extras + documentation

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update dependency extras**

In `pyproject.toml`, replace the existing `ocr` and `image` extras and the `all`
extra with:

```toml
ocr = ["pytesseract>=0.3.10", "Pillow>=10.0"]
ocr-ml = ["surya-ocr>=0.6"]
image = ["Pillow>=10.0", "opencv-python>=4.9"]
all = [
    "doc-shape-shifter[pandoc,docling,markitdown,tabula,mathpix,ocr]",
]
```

- [ ] **Step 2: Install and run the full unit suite**

Run:
```bash
uv pip install -e ".[ocr]"
uv run pytest tests/unit/ -v
```
Expected: PASS (tiling/assemble/engine tests now run rather than skip).

- [ ] **Step 3: Document the new capability**

In `README.md`, add image/OCR usage near the other CLI examples:

```markdown
### Image / Screenshot OCR (e.g. GoFullPage captures)

Convert a full-page PNG screenshot into a text-based PDF, Markdown, or text:

```bash
dss capture.png out.pdf                 # searchable PDF (image + hidden text)
dss capture.png out.pdf --mode reflow   # clean reflowed text PDF
dss capture.png --to md                 # OCR -> Markdown
dss capture.png --to txt                # OCR -> plain text
dss capture.png out.pdf --page-size a4 --dpi 300 --ocr-lang eng+fra
dss capture.png out.pdf --ocr-engine surya   # higher-accuracy engine (opt-in)
```

Requires the `tesseract` binary plus `pip install 'doc-shape-shifter[ocr]'`
(or `[ocr-ml]` for the Surya engine).
```

In `CLAUDE.md`, add a row to the backend table:

```markdown
| ocr | `ocr_backend.py` | Image (PNG/JPG/...) -> searchable/reflow PDF, md, txt via Tesseract (default) or Surya |
```

And under **System Dependencies**, append:

```markdown
For image OCR: `tesseract` (the `tesseract-ocr` binary). Optional: `surya-ocr` (`[ocr-ml]` extra) for higher accuracy.
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml README.md CLAUDE.md
git commit -m "build/docs: add ocr/ocr-ml extras and document image OCR"
```

---

### Task 12: End-to-end integration tests + fixtures

**Files:**
- Create: `tests/integration/test_ocr_pipeline.py`
- Test: (this file is the test)

> Real OCR requires the `tesseract` binary. These tests skip cleanly when it is
> absent (mirrors the pandoc-skip pattern used elsewhere in the suite).

- [ ] **Step 1: Write the integration tests (with an inline fixture builder)**

Create `tests/integration/test_ocr_pipeline.py`:

```python
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
```

- [ ] **Step 2: Run the integration tests**

Run: `uv run pytest tests/integration/test_ocr_pipeline.py -v`
Expected: PASS if `tesseract` is installed; otherwise the whole module SKIPS.

- [ ] **Step 3: Run the full suite + lint**

Run:
```bash
uv run pytest
uv run ruff check src/ tests/
```
Expected: all tests pass (or skip where deps absent); ruff clean.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_ocr_pipeline.py
git commit -m "test(ocr): end-to-end image OCR integration tests with fixtures"
```

---

## Self-Review

**Spec coverage:**
- Both PDF modes (searchable/reflow) → Tasks 6, 8, 12.
- Pluggable engine (Tesseract default + Surya opt-in) → Tasks 7, 9; selected via `ConversionOptions.ocr_engine` (Task 3) and `--ocr-engine` (Task 10).
- Letter/A4 page slicing → Task 5.
- Outputs PDF + Markdown + plain text → Task 8 (matrix entries Task 4).
- `IMAGE` format + detection → Tasks 1, 2.
- Options channel without breaking existing backends → Task 3.
- No new PDF dep (PyMuPDF reuse) → Task 6.
- Error handling (missing tesseract / unknown engine / empty OCR / decompression bomb) → Tasks 5 (MAX_IMAGE_PIXELS), 8.
- CLI flags + `--list-formats`/`--list-backends` surfacing → Tasks 8, 10.
- Dependencies/docs → Task 11.
- Testing (unit + integration + fixtures, skip-if-no-tesseract) → all tasks + Task 12.

**Placeholder scan:** No TBD/TODO; every code step contains complete code. The only
runtime-verification note is the Surya import paths (Task 9), which is an honest
version-compatibility caveat with a concrete check command, not a placeholder.

**Type consistency:** `ConversionOptions` fields (`mode`, `ocr_engine`, `page_size`,
`dpi`, `ocr_lang`) are used identically in Tasks 3, 8, 10. `OCRPage`/`OCRWord` defined
in Task 7 and consumed in Tasks 6 (`sandwich_page_pdf`), 7, 9. `Tile.image` defined in
Task 5, consumed in Task 8. `get_engine`, `slice_image`, `merge_pdf_pages`,
`render_text_pdf`, `sandwich_page_pdf`, `tile_to_pdf`, `recognize` names are consistent
across tasks.
