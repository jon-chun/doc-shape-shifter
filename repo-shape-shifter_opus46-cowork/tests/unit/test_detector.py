"""Tests for format detection module."""

import json
import pytest
from pathlib import Path

from doc_shape_shifter.detector import detect_format, UnsupportedFormatError
from doc_shape_shifter.utils.formats import DocFormat


@pytest.fixture
def tmp_files(tmp_path):
    """Create sample files for each format."""
    files = {}

    # Markdown
    md = tmp_path / "test.md"
    md.write_text("# Hello\n\nThis is [a link](http://example.com)\n\n```python\nprint('hi')\n```")
    files["md"] = md

    # Plain text
    txt = tmp_path / "test.txt"
    txt.write_text("Just some plain text content.")
    files["txt"] = txt

    # HTML
    html = tmp_path / "test.html"
    html.write_text("<!DOCTYPE html><html><body><h1>Hello</h1></body></html>")
    files["html"] = html

    # JSON
    js = tmp_path / "test.json"
    js.write_text(json.dumps({"key": "value", "items": [1, 2, 3]}))
    files["json"] = js

    # CSV
    csv = tmp_path / "test.csv"
    csv.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n")
    files["csv"] = csv

    # LaTeX
    tex = tmp_path / "test.tex"
    tex.write_text("\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")
    files["latex"] = tex

    # RTF
    rtf = tmp_path / "test.rtf"
    rtf.write_text("{\\rtf1\\ansi Hello RTF}")
    files["rtf"] = rtf

    return files


class TestExtensionDetection:
    def test_markdown(self, tmp_files):
        assert detect_format(tmp_files["md"]) == DocFormat.MARKDOWN

    def test_plain_text(self, tmp_files):
        assert detect_format(tmp_files["txt"]) == DocFormat.PLAIN_TEXT

    def test_html(self, tmp_files):
        assert detect_format(tmp_files["html"]) == DocFormat.HTML

    def test_json(self, tmp_files):
        assert detect_format(tmp_files["json"]) == DocFormat.JSON

    def test_csv(self, tmp_files):
        assert detect_format(tmp_files["csv"]) == DocFormat.CSV

    def test_latex(self, tmp_files):
        assert detect_format(tmp_files["latex"]) == DocFormat.LATEX

    def test_rtf(self, tmp_files):
        assert detect_format(tmp_files["rtf"]) == DocFormat.RTF


class TestHeuristicDetection:
    def test_latex_without_extension(self, tmp_path):
        f = tmp_path / "noext"
        f.write_text("\\documentclass{article}\n\\begin{document}\nContent\n\\end{document}")
        assert detect_format(f) == DocFormat.LATEX

    def test_html_without_extension(self, tmp_path):
        f = tmp_path / "noext"
        f.write_text("<!DOCTYPE html><html><body>Hi</body></html>")
        assert detect_format(f) == DocFormat.HTML

    def test_json_without_extension(self, tmp_path):
        f = tmp_path / "noext"
        f.write_text('{"key": "value"}')
        assert detect_format(f) == DocFormat.JSON

    def test_rtf_without_extension(self, tmp_path):
        f = tmp_path / "noext"
        f.write_text("{\\rtf1 Hello}")
        assert detect_format(f) == DocFormat.RTF


class TestEdgeCases:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            detect_format(Path("/nonexistent/file.pdf"))

    def test_unknown_format(self, tmp_path):
        f = tmp_path / "mystery.xyz"
        f.write_bytes(b"\x00\x01\x02\x03")
        with pytest.raises(UnsupportedFormatError):
            detect_format(f)
