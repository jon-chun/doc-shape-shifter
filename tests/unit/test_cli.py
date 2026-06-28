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


def test_invalid_mode_rejected():
    result = CliRunner().invoke(main, ["x.png", "y.pdf", "--mode", "bogus"])
    assert result.exit_code != 0
