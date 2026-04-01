"""Integration tests: conversions with progress and estimation enabled."""

import shutil
from pathlib import Path

import pytest

from doc_shape_shifter.converter import convert

FIXTURES = Path(__file__).parent.parent / "fixtures"

has_pandoc = shutil.which("pandoc") is not None


class TestBuiltinWithProgress:
    """Builtin conversions with show_progress=True."""

    def test_md_to_txt_with_progress(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.md", out, target_format="txt", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None
        assert r.estimated_seconds > 0
        assert r.duration_seconds > 0

    def test_json_to_csv_with_progress(self, tmp_path):
        out = tmp_path / "out.csv"
        r = convert(FIXTURES / "sample.json", out, target_format="csv", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_csv_to_json_with_progress(self, tmp_path):
        out = tmp_path / "out.json"
        r = convert(FIXTURES / "sample.csv", out, target_format="json", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_html_to_txt_with_progress(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.html", out, target_format="txt", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_txt_to_md_with_progress(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.txt", out, target_format="md", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_json_to_txt_with_progress(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.json", out, target_format="txt", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_csv_to_txt_with_progress(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.csv", out, target_format="txt", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_html_to_csv_with_progress(self, tmp_path):
        out = tmp_path / "out.csv"
        r = convert(FIXTURES / "sample.html", out, target_format="csv", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None


class TestBuiltinWithoutProgress:
    """Same conversions with show_progress=False (default) still work."""

    def test_md_to_txt_no_progress(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.md", out, target_format="txt", show_progress=False)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None


@pytest.mark.skipif(not has_pandoc, reason="pandoc not installed")
class TestPandocWithProgress:
    """Pandoc conversions with progress bar."""

    def test_md_to_html_progress(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.md", out, target_format="html", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None
        assert r.estimated_seconds > 0

    def test_md_to_docx_progress(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.md", out, target_format="docx", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_html_to_md_progress(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.html", out, target_format="md", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_md_to_latex_progress(self, tmp_path):
        out = tmp_path / "out.tex"
        r = convert(FIXTURES / "sample.md", out, target_format="latex", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_latex_to_html_progress(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.tex", out, target_format="html", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_txt_to_html_progress(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.txt", out, target_format="html", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_txt_to_docx_progress(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.txt", out, target_format="docx", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_md_to_epub_progress(self, tmp_path):
        out = tmp_path / "out.epub"
        r = convert(FIXTURES / "sample.md", out, target_format="epub", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_md_to_rtf_progress(self, tmp_path):
        out = tmp_path / "out.rtf"
        r = convert(FIXTURES / "sample.md", out, target_format="rtf", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_html_to_docx_progress(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.html", out, target_format="docx", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_latex_to_md_progress(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.tex", out, target_format="md", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_csv_to_html_progress(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.csv", out, target_format="html", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_html_to_epub_progress(self, tmp_path):
        out = tmp_path / "out.epub"
        r = convert(FIXTURES / "sample.html", out, target_format="epub", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_html_to_latex_progress(self, tmp_path):
        out = tmp_path / "out.tex"
        r = convert(FIXTURES / "sample.html", out, target_format="latex", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None

    def test_latex_to_docx_progress(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.tex", out, target_format="docx", show_progress=True)
        assert r.success, r.error_message
        assert r.estimated_seconds is not None


class TestEstimateInResult:
    """Verify estimated_seconds is always populated on success."""

    def test_estimate_populated_builtin(self, tmp_path):
        out = tmp_path / "out.csv"
        r = convert(FIXTURES / "sample.json", out, target_format="csv")
        assert r.success
        assert r.estimated_seconds is not None
        assert r.estimated_seconds > 0

    @pytest.mark.skipif(not has_pandoc, reason="pandoc not installed")
    def test_estimate_populated_pandoc(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.md", out, target_format="html")
        assert r.success
        assert r.estimated_seconds is not None
        assert r.estimated_seconds > 0

    def test_estimate_none_on_failure(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.md", out, target_format="md")
        assert not r.success
        # estimated_seconds is None because no backend ran
        assert r.estimated_seconds is None
