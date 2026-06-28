"""Tests for the format utility module."""

import pytest

from doc_shape_shifter.utils.formats import (
    EXTENSION_MAP,
    FORMAT_EXTENSION,
    MIME_MAP,
    DocFormat,
    format_from_string,
)


class TestFormatFromString:
    def test_direct_values(self):
        assert format_from_string("pdf") == DocFormat.PDF
        assert format_from_string("md") == DocFormat.MARKDOWN
        assert format_from_string("txt") == DocFormat.PLAIN_TEXT
        assert format_from_string("html") == DocFormat.HTML
        assert format_from_string("json") == DocFormat.JSON
        assert format_from_string("csv") == DocFormat.CSV
        assert format_from_string("latex") == DocFormat.LATEX
        assert format_from_string("epub") == DocFormat.EPUB
        assert format_from_string("rtf") == DocFormat.RTF
        assert format_from_string("docx") == DocFormat.DOCX

    def test_case_insensitive(self):
        assert format_from_string("PDF") == DocFormat.PDF
        assert format_from_string("Md") == DocFormat.MARKDOWN

    def test_with_dot_prefix(self):
        assert format_from_string(".pdf") == DocFormat.PDF
        assert format_from_string(".md") == DocFormat.MARKDOWN

    def test_extension_aliases(self):
        assert format_from_string("htm") == DocFormat.HTML
        assert format_from_string("markdown") == DocFormat.MARKDOWN
        assert format_from_string("text") == DocFormat.PLAIN_TEXT
        assert format_from_string("tex") == DocFormat.LATEX

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown format"):
            format_from_string("xyz")


class TestMappingConsistency:
    # SOURCE_ONLY_FORMATS are valid input formats but have no default output extension.
    SOURCE_ONLY_FORMATS = {DocFormat.IMAGE}

    def test_every_format_has_extension(self):
        for fmt in DocFormat:
            if fmt in self.SOURCE_ONLY_FORMATS:
                continue
            assert fmt in FORMAT_EXTENSION, f"{fmt} missing from FORMAT_EXTENSION"

    def test_every_extension_maps_to_format(self):
        for ext, fmt in EXTENSION_MAP.items():
            assert ext.startswith("."), f"Extension should start with dot: {ext}"
            assert isinstance(fmt, DocFormat)

    def test_every_format_is_roundtrippable(self):
        for fmt in DocFormat:
            if fmt in self.SOURCE_ONLY_FORMATS:
                continue
            ext = FORMAT_EXTENSION[fmt]
            assert EXTENSION_MAP[ext] == fmt, (
                f"Roundtrip failed: {fmt} -> {ext} -> {EXTENSION_MAP.get(ext)}"
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
