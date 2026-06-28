"""Tests for backend registry and base classes."""

import pytest

from doc_shape_shifter.backends import get_backend, list_backends
from doc_shape_shifter.backends.base import BaseBackend, ConversionResult


class TestBackendRegistry:
    def test_list_backends_returns_all(self):
        backends = list_backends()
        names = [name for name, _ in backends]
        assert "builtin" in names
        assert "pandoc" in names
        assert "pymupdf" in names
        assert "docling" in names
        assert "markitdown" in names
        assert "tabula" in names
        assert "mathpix" in names

    def test_get_builtin(self):
        be = get_backend("builtin")
        assert isinstance(be, BaseBackend)
        assert be.is_available()
        assert be.name == "builtin"

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown backend"):
            get_backend("does_not_exist")

    def test_singleton(self):
        a = get_backend("builtin")
        b = get_backend("builtin")
        assert a is b


class TestPandocBackendFormats:
    """Regression: 'plain' is not a valid pandoc input format."""

    def test_plain_text_not_used_as_input_format(self):
        from doc_shape_shifter.backends.pandoc_backend import _PANDOC_FORMATS, PandocBackend

        # "plain" should exist in the format map (for output)
        assert _PANDOC_FORMATS.get("txt") == "plain"
        # But PandocBackend.convert should handle it gracefully as input
        be = PandocBackend()
        if be.is_available():
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as tmp:
                inp = Path(tmp) / "test.txt"
                inp.write_text("Hello world")
                out = Path(tmp) / "test.html"
                r = be.convert(inp, out, "txt", "html")
                assert r.success, f"Pandoc txt->html should work, got: {r.error_message}"


class TestPandocPdfEngine:
    """Regression: pandoc must use a Unicode-aware PDF engine for PDF output.

    The default engine (pdflatex) cannot typeset arbitrary Unicode characters
    (e.g. U+2194 LEFT RIGHT ARROW), so md -> pdf failed. xelatex/lualatex/
    tectonic handle Unicode natively.
    """

    def test_build_cmd_adds_pdf_engine_for_pdf(self):
        from pathlib import Path

        from doc_shape_shifter.backends.pandoc_backend import PandocBackend

        cmd = PandocBackend._build_cli_cmd(
            Path("in.md"), Path("out.pdf"), "markdown", "pdf", pdf_engine="xelatex"
        )
        assert "--pdf-engine=xelatex" in cmd

    def test_build_cmd_no_pdf_engine_for_non_pdf(self):
        from pathlib import Path

        from doc_shape_shifter.backends.pandoc_backend import PandocBackend

        cmd = PandocBackend._build_cli_cmd(
            Path("in.md"), Path("out.html"), "markdown", "html", pdf_engine="xelatex"
        )
        assert not any(c.startswith("--pdf-engine") for c in cmd)

    def test_select_pdf_engine_prefers_unicode_engine(self, monkeypatch):
        import doc_shape_shifter.backends.pandoc_backend as pb

        # Only xelatex + lualatex present -> must pick a Unicode-aware one, never pdflatex.
        monkeypatch.setattr(
            pb.shutil,
            "which",
            lambda name: f"/usr/bin/{name}" if name in {"xelatex", "lualatex"} else None,
        )
        engine = pb._select_pdf_engine()
        assert engine in {"xelatex", "lualatex", "tectonic"}
        assert engine != "pdflatex"

    def test_select_pdf_engine_none_when_unavailable(self, monkeypatch):
        import doc_shape_shifter.backends.pandoc_backend as pb

        monkeypatch.setattr(pb.shutil, "which", lambda name: None)
        assert pb._select_pdf_engine() is None


class TestConversionResult:
    def test_str_success(self):
        r = ConversionResult(
            success=True,
            output_path=None,
            backend_name="test",
            duration_seconds=1.5,
            source_format="md",
            target_format="txt",
        )
        assert "OK" in str(r)

    def test_str_failure(self):
        r = ConversionResult(
            success=False,
            output_path=None,
            backend_name="test",
            duration_seconds=0.1,
            source_format="md",
            target_format="txt",
            error_message="broke",
        )
        assert "FAILED" in str(r)


# ---------------------------------------------------------------------------
# Task 3: ConversionOptions tests
# ---------------------------------------------------------------------------

from doc_shape_shifter.backends.base import ConversionOptions  # noqa: E402
from doc_shape_shifter.backends.builtin_backend import BuiltinBackend  # noqa: E402


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
