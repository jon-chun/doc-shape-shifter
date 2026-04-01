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


class TestConversionResult:
    def test_str_success(self):
        r = ConversionResult(
            success=True, output_path=None, backend_name="test",
            duration_seconds=1.5, source_format="md", target_format="txt",
        )
        assert "OK" in str(r)

    def test_str_failure(self):
        r = ConversionResult(
            success=False, output_path=None, backend_name="test",
            duration_seconds=0.1, source_format="md", target_format="txt",
            error_message="broke",
        )
        assert "FAILED" in str(r)
