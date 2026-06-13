# Design: Image OCR Pipeline — GoFullPage PNG → Text-Based PDF (+ Markdown/Text)

**Date:** 2026-06-13
**Status:** Approved (design phase)
**Author:** brainstorming session

## 1. Problem

doc-shape-shifter cannot today accept an image (e.g. a `*.png` produced by the
Chrome **GoFullPage** extension, which stitches a full scrolling webpage into one
very tall PNG) and produce a **text-based PDF**. Five independent blockers exist
in the current code:

1. **PNG is not a recognized format.** `DocFormat` (`utils/formats.py:6-21`) has no
   image member; `EXTENSION_MAP` / `MIME_MAP` have no image entries; `detector.py`
   has no image magic-byte check. `detect_format()` raises `UnsupportedFormatError`.
2. **No image-source route.** `CONVERSION_MATRIX` (`router.py:23-109`) has zero
   image-source entries; `get_backend_chain()` would raise `UnsupportedConversionError`.
3. **No backend produces a searchable PDF from an image.** Only `mathpix` accepts
   images (`mathpix_backend.py:56`) and it emits LaTeX only, via a paid cloud API.
4. **No "text-layer PDF" concept exists.** Every PDF *target* is produced by Pandoc
   from already-textual sources.
5. **GoFullPage-specific:** captures are single, extremely tall stitched PNGs
   (often 10k–50k+ px), which hit PIL decompression-bomb / OCR input-size limits and
   would yield one unusable giant page without tiling.

The architecture already *anticipates* this: `pipelines/__init__.py` documents a
planned `ocr` pipeline (MinerU/Marker/Surya/Tesseract) and `image` pipeline, and
`pyproject.toml` declares `ocr` and `image` optional-dependency groups
(`lines 44-45`). They are empty stubs — no implementation.

## 2. Goals

- Convert a raster image (PNG and common siblings) into a **text-based PDF** in two
  user-selectable modes:
  - **searchable** — keep the exact capture as the visible page + an invisible OCR
    text layer (selectable / searchable / copyable). *(default)*
  - **reflow** — extract OCR text and render a clean flowing text-document PDF.
- Also expose the OCR text as **Markdown** and **plain text** targets (near-free,
  high value for the project's stated RAG/search use case).
- Handle the tall GoFullPage capture by slicing it into standard **Letter/A4** pages.
- Local-first: default to **Tesseract**; allow opt-in **Surya** for higher accuracy.
- Reuse the existing detect → route → convert → fallback pipeline, CLI, and result
  reporting unchanged.

## 3. Non-Goals (v1 — YAGNI)

- Smart whitespace/element break-point detection (default fixed-height slicing only).
- OpenCV preprocessing / deskew / denoise (capture text is pixel-perfect rendered,
  not photographed; not needed for v1).
- Cloud OCR (Mathpix and similar).
- Multi-file / folder batch merge into one PDF.
- Image-only **PDF** → searchable PDF (the architecture will enable this later for
  ~free, but it is out of scope now).
- HTML / DOCX / JSON image-source targets (only PDF / MD / TXT in v1).

## 4. Chosen Approach — Hybrid (C)

Engine adapters, image tiling, and PDF assembly live in the documented
`pipelines/` home; a thin `OCRBackend(BaseBackend)` adapts them into the existing
conversion matrix. This honors both the backend convention (so `convert()`, router,
CLI, `--list-formats`, and fallback keep working) and the planned pipeline
structure, while keeping engine logic isolated and independently unit-testable.

Approaches A (matrix-only, OCR logic inside `backends/`) and B (separate pipeline
bypassing the matrix) were rejected: A crowds `backends/` and loses isolation; B
duplicates orchestration and creates two parallel code paths.

## 5. Architecture & Module Layout

### 5.1 New / changed files

| File | Change |
|------|--------|
| `utils/formats.py` | Add `IMAGE = "image"` to `DocFormat`; map `.png/.jpg/.jpeg/.webp/.tiff/.tif/.bmp` and image MIME types (`image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp`) to `DocFormat.IMAGE`. **Do not** add `IMAGE` to `FORMAT_EXTENSION` (never an output format). |
| `detector.py` | Add image magic-byte heuristics: PNG `\x89PNG\r\n`, JPEG `\xFF\xD8\xFF`, GIF (ignored), BMP `BM`, TIFF `II*\x00`/`MM\x00*`, WEBP `RIFF....WEBP`. |
| `router.py` | Add matrix entries: `(IMAGE, PDF) → ["ocr"]`, `(IMAGE, MARKDOWN) → ["ocr"]`, `(IMAGE, PLAIN_TEXT) → ["ocr"]`. |
| `backends/base.py` | Add `ConversionOptions` dataclass; add `options: ConversionOptions \| None = None` to `BaseBackend.convert()`. |
| `backends/__init__.py` | Register `OCRBackend` in `_register_backends()`. |
| `backends/ocr_backend.py` | **New.** Orchestrates tiling → engine → assemble; reads `options`; `is_available()` = `shutil.which("tesseract")` present **and** `pytesseract` importable (engine-aware). |
| `pipelines/image/tiling.py` | **New.** Load image, raise `Image.MAX_IMAGE_PIXELS` with a guarded cap, scale to page width at target DPI, slice into page-height tiles. |
| `pipelines/ocr/engines/base.py` | **New.** `OCREngine` ABC. |
| `pipelines/ocr/engines/tesseract.py` | **New.** Tesseract adapter. |
| `pipelines/ocr/engines/surya.py` | **New.** Surya adapter (opt-in). |
| `pipelines/ocr/assemble.py` | **New.** Build searchable PDF (merge tile PDFs) and reflow PDF (render text) via PyMuPDF. |
| `cli.py` | Add `--mode`, `--ocr-engine`, `--page-size`, `--dpi`, `--ocr-lang`; build `ConversionOptions`. |
| `converter.py` | Add `options` param; thread it through `_run_with_progress` → `be.convert()`. |
| `pyproject.toml` | Restructure extras: `ocr = ["pytesseract>=0.3.10", "Pillow>=10.0"]`; `ocr-ml = ["surya-ocr>=0.6"]`; add `ocr` to `all`. |

### 5.2 Interfaces

```python
# backends/base.py
@dataclass
class ConversionOptions:
    mode: str = "searchable"        # "searchable" | "reflow"
    ocr_engine: str = "tesseract"   # "tesseract" | "surya"
    page_size: str = "letter"       # "letter" | "a4" | "continuous"
    dpi: int = 200
    ocr_lang: str = "eng"

# pipelines/ocr/engines/base.py
@dataclass
class OCRWord:
    text: str
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1 in tile pixels

@dataclass
class OCRPage:
    text: str
    words: list[OCRWord]            # may be empty for text-only engines

class OCREngine(ABC):
    name: str
    def is_available(self) -> bool: ...
    def recognize(self, tile: "PIL.Image.Image", lang: str) -> OCRPage: ...
    def tile_to_pdf(self, tile: "PIL.Image.Image", lang: str) -> bytes:
        """Single-page sandwich PDF (image + invisible text). Default impl may
        build from recognize() + assemble; Tesseract overrides via
        image_to_pdf_or_hocr for fidelity."""
```

`BaseBackend.convert()` signature becomes:

```python
def convert(self, input_path, output_path, source_format, target_format,
            options: ConversionOptions | None = None) -> ConversionResult: ...
```

The 6 existing backends add the parameter and ignore it (backward-compatible).

## 6. Data Flow

```
detect_format() → DocFormat.IMAGE
   → get_backend_chain(IMAGE, target) → ["ocr"]
   → OCRBackend.convert(input, output, "image", target, options)
        → tiling.slice_image(input, page_size, dpi) → [tile_0 … tile_n]
        → engine = select(options.ocr_engine)   # gated by is_available()
        → target == "pdf" and mode == "searchable":
              per tile: engine.tile_to_pdf(tile) → assemble.merge_pdfs() (PyMuPDF)
        → target == "pdf" and mode == "reflow":
              per tile: engine.recognize(tile).text → join
                        → assemble.render_text_pdf() (PyMuPDF text pages)
        → target in ("md", "txt"):
              per tile: engine.recognize(tile).text → join
                        → md prepends "# {stem}" heading; txt raw
        → ConversionResult(success, output_path, "ocr", …, warnings)
```

Notes:
- **Tiling math:** scaled_width = page_width_px(page_size, dpi); scale factor =
  scaled_width / image_width; tile_height_px = page_height_px(page_size, dpi);
  number of tiles = ceil(scaled_image_height / tile_height_px). Slices are
  **non-overlapping** (each tile's invisible text layer maps cleanly to that tile's
  image region; overlap would duplicate boundary text). `page_size == "continuous"`
  yields a single tile / single tall page (degenerate, allowed).
- **Searchable assembly:** Tesseract's `image_to_pdf_or_hocr(tile, extension="pdf")`
  already emits a per-tile sandwich page; PyMuPDF (`fitz`, core dep) merges them.
- **Reflow assembly:** PyMuPDF creates blank Letter/A4 pages and flows text via
  `page.insert_textbox`, paginating overflow. No Pandoc/LaTeX dependency.

## 7. CLI

```
dss capture.png out.pdf                         # searchable PDF (default)
dss capture.png out.pdf --mode reflow           # reflowed text PDF
dss capture.png --to md                          # OCR → Markdown
dss capture.png --to txt                         # OCR → plain text
dss capture.png out.pdf --ocr-engine surya --ocr-lang eng+fra
dss capture.png out.pdf --page-size a4 --dpi 300
```

New options surface in `--help`; `--list-formats` shows the three new
`image → {pdf, md, txt}` pairs; `--list-backends` shows `ocr` with availability
(Tesseract binary detected or not) and version.

## 8. Error Handling

- **Tesseract binary missing:** `OCRBackend.is_available()` returns False (checks
  `shutil.which("tesseract")` + `pytesseract` import) → standard "not installed"
  fallback messaging; error hint: "install tesseract-ocr".
- **`--ocr-engine surya` but Surya not installed:** `ConversionResult(success=False)`
  with install hint (`pip install 'doc-shape-shifter[ocr-ml]'`).
- **Decompression-bomb guard:** raise `Image.MAX_IMAGE_PIXELS` to a generous,
  explicit cap; if exceeded, fail with a clear message rather than crash.
- **Empty OCR result:** succeed with a `warnings` entry (mirrors
  `pymupdf_backend.py:97-102`), e.g. "OCR produced no text — image may be blank".
- **Invalid `--mode` / `--page-size`:** validated by `click.Choice`.

## 9. Dependencies

| Group | Packages | Notes |
|-------|----------|-------|
| `ocr` (default engine) | `pytesseract>=0.3.10`, `Pillow>=10.0` | + system `tesseract-ocr` binary |
| `ocr-ml` (opt-in) | `surya-ocr>=0.6` | pulls PyTorch; high accuracy |
| (reused, core) | `pymupdf` | merge + render PDFs; no new PDF dep |

`all` extra gains `ocr`. README/CLAUDE.md "System Dependencies" gains `tesseract`.

## 10. Testing

**Unit (`tests/unit/`):**
- `test_detector`: `.png/.jpg/.webp/.tiff/.bmp` and magic bytes → `DocFormat.IMAGE`.
- `test_router`: new `(IMAGE, {PDF,MD,TXT})` entries resolve to `["ocr"]`.
- `test_formats`: extension/MIME maps include image types; `IMAGE` absent from
  `FORMAT_EXTENSION`.
- `test_backends`: `ConversionOptions` defaults; `OCRBackend.is_available()` gating
  (monkeypatch `shutil.which`); non-OCR backends still accept the new `options` kwarg.
- `test_tiling`: tile-count math for known image-height / page-size / dpi inputs;
  non-overlap invariants; `continuous` → 1 tile.

**Integration (`tests/integration/`):** *(skipped if `tesseract` binary absent —
mirrors the pandoc-skip pattern)*
- Small known-text PNG fixture → searchable PDF; assert text is extractable via
  `fitz` `page.get_text()` and matches expected words.
- Same PNG → `.md` / `.txt`; assert expected text present.
- Same PNG → reflow PDF; assert it renders and contains the text.
- **Tall synthetic multi-section PNG** fixture → assert output PDF has the expected
  multi-page count (tiling correctness).

**Fixtures (`tests/fixtures/`):** add `sample_text.png` (small, known words) and
`tall_capture.png` (synthetic, generatable via PIL in a fixture builder).

## 11. Locked Defaults

- mode = `searchable`, engine = `tesseract`, page_size = `letter`, dpi = `200`,
  lang = `eng`.

## 12. Acceptance Criteria

1. `dss capture.png out.pdf` produces a PDF whose text is selectable/searchable and
   matches the capture content (searchable mode).
2. `dss capture.png out.pdf --mode reflow` produces a clean multi-page text PDF.
3. `dss capture.png --to md` and `--to txt` produce the OCR text.
4. A tall GoFullPage-style PNG yields a correctly paginated multi-page Letter PDF
   (no decompression-bomb crash, no single giant page).
5. With no Tesseract installed, the conversion fails gracefully with an install hint;
   all existing (non-image) conversions and tests are unaffected.
6. `--list-formats` and `--list-backends` reflect the new capability.
