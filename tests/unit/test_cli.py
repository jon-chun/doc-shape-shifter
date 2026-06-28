"""Tests for CLI flags added in Task 10 (OCR options)."""

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


def test_invalid_mode_rejected(tmp_path):
    src = tmp_path / "x.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\n")
    result = CliRunner().invoke(main, [str(src), str(tmp_path / "y.pdf"), "--mode", "bogus"])
    assert result.exit_code != 0
    # Must fail specifically because of the invalid --mode choice, not file-not-found.
    assert "bogus" in result.output or "Invalid value" in result.output
