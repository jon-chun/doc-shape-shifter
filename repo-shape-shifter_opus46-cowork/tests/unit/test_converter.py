"""Tests for the main converter orchestration module."""

import json
import pytest
from pathlib import Path

from doc_shape_shifter.converter import convert


@pytest.fixture
def sample_md(tmp_path):
    f = tmp_path / "sample.md"
    f.write_text("# Title\n\nSome **bold** and *italic* text.\n\n- Item 1\n- Item 2\n")
    return f


@pytest.fixture
def sample_json(tmp_path):
    f = tmp_path / "sample.json"
    f.write_text(json.dumps([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]))
    return f


@pytest.fixture
def sample_csv(tmp_path):
    f = tmp_path / "sample.csv"
    f.write_text("name,age\nAlice,30\nBob,25\n")
    return f


@pytest.fixture
def sample_html(tmp_path):
    f = tmp_path / "sample.html"
    f.write_text("<html><body><h1>Title</h1><p>Paragraph text.</p></body></html>")
    return f


class TestBuiltinConversions:
    """Test conversions that use the builtin backend (always available)."""

    def test_md_to_txt(self, sample_md, tmp_path):
        out = tmp_path / "output.txt"
        result = convert(sample_md, out, target_format="txt")
        assert result.success
        assert out.exists()
        content = out.read_text()
        assert "Title" in content
        assert "**" not in content  # Markdown stripped

    def test_json_to_csv(self, sample_json, tmp_path):
        out = tmp_path / "output.csv"
        result = convert(sample_json, out, target_format="csv")
        assert result.success
        content = out.read_text()
        assert "name" in content
        assert "Alice" in content

    def test_csv_to_json(self, sample_csv, tmp_path):
        out = tmp_path / "output.json"
        result = convert(sample_csv, out, target_format="json")
        assert result.success
        data = json.loads(out.read_text())
        assert isinstance(data, list)
        assert data[0]["name"] == "Alice"

    def test_html_to_txt(self, sample_html, tmp_path):
        out = tmp_path / "output.txt"
        result = convert(sample_html, out, target_format="txt")
        assert result.success
        content = out.read_text()
        assert "Title" in content
        assert "<html>" not in content


class TestAutoOutputPath:
    def test_auto_generates_output(self, sample_md):
        result = convert(sample_md, target_format="txt")
        assert result.success
        assert result.output_path is not None
        assert result.output_path.suffix == ".txt"
        # Cleanup
        result.output_path.unlink(missing_ok=True)


class TestErrorHandling:
    def test_missing_target_format(self, sample_md):
        with pytest.raises(ValueError, match="Target format is required"):
            convert(sample_md)

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            convert("/nonexistent/file.md", target_format="txt")

    def test_same_format(self, sample_md, tmp_path):
        out = tmp_path / "output.md"
        result = convert(sample_md, out, target_format="md")
        assert not result.success
        assert "same" in result.error_message.lower()


class TestForcedBackend:
    def test_force_builtin(self, sample_md, tmp_path):
        out = tmp_path / "output.txt"
        result = convert(sample_md, out, target_format="txt", backend="builtin")
        assert result.success
        assert result.backend_name == "builtin"

    def test_force_unknown_backend(self, sample_md, tmp_path):
        out = tmp_path / "output.txt"
        result = convert(sample_md, out, target_format="txt", backend="nonexistent")
        assert not result.success


class TestConversionResult:
    def test_result_metadata(self, sample_md, tmp_path):
        out = tmp_path / "output.txt"
        result = convert(sample_md, out, target_format="txt")
        assert result.source_format == "md"
        assert result.target_format == "txt"
        assert result.duration_seconds > 0
        assert result.file_size_bytes is not None
        assert result.file_size_bytes > 0
