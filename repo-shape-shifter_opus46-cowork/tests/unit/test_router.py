"""Tests for the conversion routing module."""

import pytest
from doc_shape_shifter.router import (
    get_backend_chain,
    list_supported_conversions,
    UnsupportedConversionError,
)
from doc_shape_shifter.utils.formats import DocFormat


class TestGetBackendChain:
    def test_pdf_to_markdown(self):
        chain = get_backend_chain(DocFormat.PDF, DocFormat.MARKDOWN)
        assert len(chain) > 0
        assert "docling" in chain or "pymupdf" in chain or "pandoc" in chain

    def test_docx_to_markdown(self):
        chain = get_backend_chain(DocFormat.DOCX, DocFormat.MARKDOWN)
        assert len(chain) > 0

    def test_csv_to_json(self):
        chain = get_backend_chain(DocFormat.CSV, DocFormat.JSON)
        assert "builtin" in chain

    def test_same_format_raises(self):
        with pytest.raises(UnsupportedConversionError):
            get_backend_chain(DocFormat.PDF, DocFormat.PDF)

    def test_html_to_plain_text(self):
        chain = get_backend_chain(DocFormat.HTML, DocFormat.PLAIN_TEXT)
        assert "builtin" in chain

    def test_pdf_to_latex(self):
        chain = get_backend_chain(DocFormat.PDF, DocFormat.LATEX)
        assert "mathpix" in chain or "pandoc" in chain


class TestListConversions:
    def test_returns_nonempty(self):
        conversions = list_supported_conversions()
        assert len(conversions) > 30  # We defined ~60+ pairs

    def test_tuple_structure(self):
        conversions = list_supported_conversions()
        for src, tgt, backends in conversions:
            assert isinstance(src, str)
            assert isinstance(tgt, str)
            assert isinstance(backends, list)
            assert len(backends) > 0
