from __future__ import annotations

import csv
import json
import tempfile
from html import escape
from html.parser import HTMLParser
from pathlib import Path

from ..core.runtime import (
    command_exists,
    command_version,
    mathpix_credentials_present,
    module_exists,
    preferred_pdf_engine,
    run_command,
)
from ..core.types import (
    DocumentFormat,
    DocumentIR,
    PANDOC_READ_FORMATS,
    PANDOC_WRITE_FORMATS,
    TableData,
    ToolAvailability,
)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self.parts)


def detect_tooling() -> dict[str, ToolAvailability]:
    pdf_engine = preferred_pdf_engine()
    return {
        "pandoc": ToolAvailability(
            name="pandoc",
            available=command_exists("pandoc"),
            detail="General text-format conversion engine",
            version=command_version(["pandoc", "--version"]),
        ),
        "docling": ToolAvailability(
            name="docling",
            available=module_exists("docling"),
            detail="Broad document parsing engine for PDF and Office formats",
        ),
        "pymupdf4llm": ToolAvailability(
            name="pymupdf4llm",
            available=module_exists("pymupdf4llm"),
            detail="Fast PDF-to-Markdown extractor",
        ),
        "tabula": ToolAvailability(
            name="tabula",
            available=module_exists("tabula") and command_exists("java"),
            detail="PDF table extraction to CSV via Java",
        ),
        "mathpix": ToolAvailability(
            name="mathpix",
            available=mathpix_credentials_present(),
            detail="Optional external OCR service for STEM-heavy documents",
        ),
        "pdf_engine": ToolAvailability(
            name="pdf_engine",
            available=pdf_engine is not None,
            detail=f"Pandoc PDF engine: {pdf_engine or 'missing'}",
            version=pdf_engine,
        ),
    }


def extract_with_native(input_path: Path, source_format: DocumentFormat) -> DocumentIR:
    if source_format == DocumentFormat.MARKDOWN:
        text = input_path.read_text(encoding="utf-8")
        return DocumentIR(
            source_path=input_path,
            source_format=source_format,
            markdown=text,
            plain_text=text,
            metadata={"engine": "native"},
        )

    if source_format == DocumentFormat.TEXT:
        text = input_path.read_text(encoding="utf-8")
        return DocumentIR(
            source_path=input_path,
            source_format=source_format,
            markdown=text,
            plain_text=text,
            metadata={"engine": "native"},
        )

    if source_format == DocumentFormat.HTML:
        html = input_path.read_text(encoding="utf-8")
        parser = _HTMLTextExtractor()
        parser.feed(html)
        plain = parser.get_text()
        return DocumentIR(
            source_path=input_path,
            source_format=source_format,
            markdown=plain,
            plain_text=plain,
            html=html,
            metadata={"engine": "native"},
        )

    if source_format == DocumentFormat.CSV:
        with input_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        table = TableData(name=input_path.stem, rows=rows)
        return DocumentIR(
            source_path=input_path,
            source_format=source_format,
            markdown=table.to_markdown(),
            plain_text="\n".join(",".join(row.values()) for row in rows),
            tables=[table],
            metadata={"engine": "native"},
        )

    if source_format == DocumentFormat.JSON:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and {"markdown", "plain_text", "html", "tables"} & payload.keys():
            tables = [
                TableData(name=item.get("name"), rows=item.get("rows", []))
                for item in payload.get("tables", [])
            ]
            return DocumentIR(
                source_path=input_path,
                source_format=source_format,
                markdown=payload.get("markdown"),
                plain_text=payload.get("plain_text"),
                html=payload.get("html"),
                tables=tables,
                metadata=payload.get("metadata", {}),
            )

        table_rows: list[dict[str, object]] = []
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            table_rows = [dict(item) for item in payload]

        tables = [TableData(name=input_path.stem, rows=table_rows)] if table_rows else []
        pretty = json.dumps(payload, indent=2, ensure_ascii=False)
        return DocumentIR(
            source_path=input_path,
            source_format=source_format,
            markdown=f"```json\n{pretty}\n```",
            plain_text=pretty,
            tables=tables,
            metadata={"engine": "native", "json_data": payload},
        )

    raise ValueError(f"Native extraction is not supported for {source_format.value}")


def extract_with_pandoc(input_path: Path, source_format: DocumentFormat) -> DocumentIR:
    read_format = PANDOC_READ_FORMATS[source_format]
    with tempfile.TemporaryDirectory() as tmpdir:
        markdown_path = Path(tmpdir) / "intermediate.md"
        command = [
            "pandoc",
            "--from",
            read_format,
            "--to",
            "gfm",
            "-o",
            str(markdown_path),
            str(input_path),
        ]
        run_command(command)
        markdown = markdown_path.read_text(encoding="utf-8")
    return DocumentIR(
        source_path=input_path,
        source_format=source_format,
        markdown=markdown,
        plain_text=markdown,
        metadata={"engine": "pandoc"},
    )


def extract_with_pymupdf(input_path: Path, force_ocr: bool = False) -> DocumentIR:
    import pymupdf4llm

    markdown = pymupdf4llm.to_markdown(
        str(input_path),
        force_ocr=force_ocr,
        use_ocr=force_ocr,
    )
    if not isinstance(markdown, str) or not markdown.strip():
        raise RuntimeError("PyMuPDF4LLM returned empty Markdown")
    return DocumentIR(
        source_path=input_path,
        source_format=DocumentFormat.PDF,
        markdown=markdown,
        plain_text=markdown,
        metadata={"engine": "pymupdf4llm", "force_ocr": force_ocr},
    )


def extract_with_docling(input_path: Path, source_format: DocumentFormat) -> DocumentIR:
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(str(input_path))
    markdown = result.document.export_to_markdown()
    if not markdown.strip():
        raise RuntimeError("Docling returned empty Markdown")
    return DocumentIR(
        source_path=input_path,
        source_format=source_format,
        markdown=markdown,
        plain_text=markdown,
        metadata={"engine": "docling"},
    )


def convert_pdf_to_csv_with_tabula(input_path: Path, output_path: Path) -> None:
    import tabula

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tabula.convert_into(str(input_path), str(output_path), output_format="csv", pages="all")


def render_with_native(ir: DocumentIR, output_path: Path, target_format: DocumentFormat) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if target_format == DocumentFormat.MARKDOWN:
        output_path.write_text(ir.markdown_text(), encoding="utf-8")
        return

    if target_format == DocumentFormat.TEXT:
        output_path.write_text(ir.plain_text_value(), encoding="utf-8")
        return

    if target_format == DocumentFormat.JSON:
        output_path.write_text(
            json.dumps(ir.as_jsonable(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return

    if target_format == DocumentFormat.HTML:
        html = ir.html
        if not html:
            html = (
                "<html><body><pre>"
                + escape(ir.markdown_text())
                + "</pre></body></html>"
            )
        output_path.write_text(html, encoding="utf-8")
        return

    if target_format == DocumentFormat.CSV:
        rows: list[dict[str, object]] = []
        if ir.tables:
            rows = ir.tables[0].rows
        else:
            json_data = ir.metadata.get("json_data")
            if isinstance(json_data, list) and json_data and isinstance(json_data[0], dict):
                rows = [dict(item) for item in json_data]
        if not rows:
            raise RuntimeError("No table-like data available for CSV rendering")
        fieldnames = list(rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return

    raise ValueError(f"Native renderer does not support {target_format.value}")


def convert_with_pandoc_direct(
    input_path: Path,
    output_path: Path,
    source_format: DocumentFormat,
    target_format: DocumentFormat,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "pandoc",
        "--from",
        PANDOC_READ_FORMATS[source_format],
    ]
    write_format = PANDOC_WRITE_FORMATS.get(target_format)
    if write_format:
        command.extend(["--to", write_format])
    if target_format == DocumentFormat.PDF:
        pdf_engine = preferred_pdf_engine()
        if not pdf_engine:
            raise RuntimeError("No PDF engine available for pandoc")
        command.extend(["--pdf-engine", pdf_engine])
    command.extend(["-o", str(output_path), str(input_path)])
    run_command(command)


def render_with_pandoc_from_ir(ir: DocumentIR, output_path: Path, target_format: DocumentFormat) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        markdown_path = Path(tmpdir) / "intermediate.md"
        markdown_path.write_text(ir.markdown_text(), encoding="utf-8")
        command = ["pandoc", "--from", "gfm"]
        write_format = PANDOC_WRITE_FORMATS.get(target_format)
        if write_format:
            command.extend(["--to", write_format])
        if target_format == DocumentFormat.PDF:
            pdf_engine = preferred_pdf_engine()
            if not pdf_engine:
                raise RuntimeError("No PDF engine available for pandoc")
            command.extend(["--pdf-engine", pdf_engine])
        command.extend(["-o", str(output_path), str(markdown_path)])
        run_command(command)
