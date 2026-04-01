"""Integration tests: actual 2-way conversions using available backends.

Tests all builtin conversions directly, and pandoc-dependent conversions
only when pandoc is available on the system.
"""

import json
import shutil
from pathlib import Path

import pytest

from doc_shape_shifter.converter import convert

FIXTURES = Path(__file__).parent.parent / "fixtures"

has_pandoc = shutil.which("pandoc") is not None


# ============================================================================
# Builtin-only conversions (always available, no external deps)
# ============================================================================


class TestBuiltinRoundTrips:
    """Test conversions that use the builtin backend exclusively."""

    def test_md_to_txt(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.md", out, target_format="txt")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Sample Document" in content
        assert "**" not in content  # markdown stripped

    def test_txt_to_md(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.txt", out, target_format="md")
        assert r.success, r.error_message
        assert out.read_text().strip()

    def test_json_to_csv(self, tmp_path):
        out = tmp_path / "out.csv"
        r = convert(FIXTURES / "sample.json", out, target_format="csv")
        assert r.success, r.error_message
        content = out.read_text()
        assert "name" in content
        assert "Alice" in content
        assert "Charlie" in content

    def test_csv_to_json(self, tmp_path):
        out = tmp_path / "out.json"
        r = convert(FIXTURES / "sample.csv", out, target_format="json")
        assert r.success, r.error_message
        data = json.loads(out.read_text())
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["name"] == "Alice"

    def test_json_to_csv_roundtrip(self, tmp_path):
        """JSON -> CSV -> JSON should preserve data."""
        csv_out = tmp_path / "step1.csv"
        r1 = convert(FIXTURES / "sample.json", csv_out, target_format="csv")
        assert r1.success, r1.error_message

        json_out = tmp_path / "step2.json"
        r2 = convert(csv_out, json_out, target_format="json")
        assert r2.success, r2.error_message

        original = json.loads((FIXTURES / "sample.json").read_text())
        roundtripped = json.loads(json_out.read_text())
        assert len(roundtripped) == len(original)
        for orig, rt in zip(original, roundtripped, strict=True):
            assert rt["name"] == orig["name"]

    def test_html_to_txt(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.html", out, target_format="txt")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Sample Document" in content
        assert "<html>" not in content

    def test_html_to_csv(self, tmp_path):
        out = tmp_path / "out.csv"
        r = convert(FIXTURES / "sample.html", out, target_format="csv")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Alice" in content

    def test_json_to_txt(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.json", out, target_format="txt")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Alice" in content

    def test_csv_to_txt(self, tmp_path):
        out = tmp_path / "out.txt"
        r = convert(FIXTURES / "sample.csv", out, target_format="txt")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Alice" in content


# ============================================================================
# Pandoc-dependent conversions
# ============================================================================


@pytest.mark.skipif(not has_pandoc, reason="pandoc not installed")
class TestPandocConversions:
    """Test conversions requiring pandoc."""

    def test_md_to_html(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.md", out, target_format="html")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Sample Document" in content

    def test_md_to_docx(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.md", out, target_format="docx")
        assert r.success, r.error_message
        assert out.stat().st_size > 0

    def test_html_to_md(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.html", out, target_format="md")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Sample Document" in content

    def test_md_to_latex(self, tmp_path):
        out = tmp_path / "out.tex"
        r = convert(FIXTURES / "sample.md", out, target_format="latex")
        assert r.success, r.error_message
        content = out.read_text()
        assert "document" in content.lower()

    def test_latex_to_html(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.tex", out, target_format="html")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Section One" in content

    def test_latex_to_md(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.tex", out, target_format="md")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Section" in content

    def test_md_to_epub(self, tmp_path):
        out = tmp_path / "out.epub"
        r = convert(FIXTURES / "sample.md", out, target_format="epub")
        assert r.success, r.error_message
        assert out.stat().st_size > 0

    def test_html_to_docx(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.html", out, target_format="docx")
        assert r.success, r.error_message
        assert out.stat().st_size > 0

    def test_md_to_rtf(self, tmp_path):
        out = tmp_path / "out.rtf"
        r = convert(FIXTURES / "sample.md", out, target_format="rtf")
        assert r.success, r.error_message
        content = out.read_text()
        assert "rtf" in content.lower() or len(content) > 0

    def test_txt_to_html(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.txt", out, target_format="html")
        assert r.success, r.error_message
        assert out.stat().st_size > 0

    def test_txt_to_docx(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.txt", out, target_format="docx")
        assert r.success, r.error_message
        assert out.stat().st_size > 0

    def test_csv_to_html(self, tmp_path):
        out = tmp_path / "out.html"
        r = convert(FIXTURES / "sample.csv", out, target_format="html")
        assert r.success, r.error_message
        content = out.read_text()
        assert "Alice" in content

    def test_md_html_roundtrip(self, tmp_path):
        """MD -> HTML -> MD should preserve key content."""
        html_out = tmp_path / "step1.html"
        r1 = convert(FIXTURES / "sample.md", html_out, target_format="html")
        assert r1.success, r1.error_message

        md_out = tmp_path / "step2.md"
        r2 = convert(html_out, md_out, target_format="md")
        assert r2.success, r2.error_message

        content = md_out.read_text()
        assert "Sample Document" in content

    def test_latex_to_docx(self, tmp_path):
        out = tmp_path / "out.docx"
        r = convert(FIXTURES / "sample.tex", out, target_format="docx")
        assert r.success, r.error_message
        assert out.stat().st_size > 0

    def test_html_to_epub(self, tmp_path):
        out = tmp_path / "out.epub"
        r = convert(FIXTURES / "sample.html", out, target_format="epub")
        assert r.success, r.error_message
        assert out.stat().st_size > 0

    def test_html_to_latex(self, tmp_path):
        out = tmp_path / "out.tex"
        r = convert(FIXTURES / "sample.html", out, target_format="latex")
        assert r.success, r.error_message
        assert out.stat().st_size > 0


# ============================================================================
# Error / edge case conversions
# ============================================================================


class TestConversionEdgeCases:
    def test_same_format_rejected(self, tmp_path):
        out = tmp_path / "out.md"
        r = convert(FIXTURES / "sample.md", out, target_format="md")
        assert not r.success
        assert "same" in r.error_message.lower()

    def test_empty_json_array(self, tmp_path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        out = tmp_path / "out.csv"
        r = convert(empty, out, target_format="csv")
        assert not r.success  # Empty array can't become CSV

    def test_nonexistent_input(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            convert(tmp_path / "does_not_exist.md", target_format="txt")
