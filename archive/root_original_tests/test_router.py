from pathlib import Path

from doc_shape_shifter.core.router import ConversionRouter
from doc_shape_shifter.core.types import ConversionRequest, DocumentFormat, ToolAvailability


def make_tooling(**overrides):
    defaults = {
        "pandoc": ToolAvailability("pandoc", True, "pandoc"),
        "docling": ToolAvailability("docling", True, "docling"),
        "pymupdf4llm": ToolAvailability("pymupdf4llm", True, "pymupdf4llm"),
        "tabula": ToolAvailability("tabula", True, "tabula"),
        "mathpix": ToolAvailability("mathpix", False, "mathpix"),
        "pdf_engine": ToolAvailability("pdf_engine", True, "pdf_engine"),
    }
    defaults.update(overrides)
    return defaults


def test_pdf_to_csv_prefers_tabula():
    router = ConversionRouter(tooling=make_tooling())
    request = ConversionRequest(
        input_path=Path("input.pdf"),
        output_path=Path("output.csv"),
        source_format=DocumentFormat.PDF,
        target_format=DocumentFormat.CSV,
    )
    plans = router.rank_plans(request)
    assert plans[0].direct_engine == "tabula"


def test_markdown_to_docx_prefers_pandoc_direct():
    router = ConversionRouter(tooling=make_tooling())
    request = ConversionRequest(
        input_path=Path("input.md"),
        output_path=Path("output.docx"),
        source_format=DocumentFormat.MARKDOWN,
        target_format=DocumentFormat.DOCX,
    )
    plans = router.rank_plans(request)
    assert plans[0].route_name == "pandoc-direct"


def test_pdf_to_docx_prefers_pymupdf_then_pandoc():
    router = ConversionRouter(tooling=make_tooling())
    request = ConversionRequest(
        input_path=Path("input.pdf"),
        output_path=Path("output.docx"),
        source_format=DocumentFormat.PDF,
        target_format=DocumentFormat.DOCX,
    )
    plans = router.rank_plans(request)
    assert plans[0].extractor == "pymupdf4llm"
    assert plans[0].renderer == "pandoc"


def test_prefer_engine_boosts_ranking():
    router = ConversionRouter(tooling=make_tooling())
    request = ConversionRequest(
        input_path=Path("input.pdf"),
        output_path=Path("output.docx"),
        source_format=DocumentFormat.PDF,
        target_format=DocumentFormat.DOCX,
        prefer_engine="docling",
    )
    plans = router.rank_plans(request)
    assert plans[0].extractor == "docling"
