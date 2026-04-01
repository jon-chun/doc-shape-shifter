from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "md"
    LATEX = "tex"
    EPUB = "epub"
    TEXT = "txt"


FORMAT_ALIASES = {
    "pdf": DocumentFormat.PDF,
    "docx": DocumentFormat.DOCX,
    "pptx": DocumentFormat.PPTX,
    "xlsx": DocumentFormat.XLSX,
    "html": DocumentFormat.HTML,
    "htm": DocumentFormat.HTML,
    "json": DocumentFormat.JSON,
    "csv": DocumentFormat.CSV,
    "md": DocumentFormat.MARKDOWN,
    "markdown": DocumentFormat.MARKDOWN,
    "gfm": DocumentFormat.MARKDOWN,
    "tex": DocumentFormat.LATEX,
    "latex": DocumentFormat.LATEX,
    "epub": DocumentFormat.EPUB,
    "txt": DocumentFormat.TEXT,
    "text": DocumentFormat.TEXT,
    "plain": DocumentFormat.TEXT,
}


PANDOC_READ_FORMATS = {
    DocumentFormat.DOCX: "docx",
    DocumentFormat.HTML: "html",
    DocumentFormat.CSV: "csv",
    DocumentFormat.MARKDOWN: "gfm",
    DocumentFormat.LATEX: "latex",
    DocumentFormat.EPUB: "epub",
}


PANDOC_WRITE_FORMATS = {
    DocumentFormat.DOCX: "docx",
    DocumentFormat.HTML: "html",
    DocumentFormat.MARKDOWN: "gfm",
    DocumentFormat.LATEX: "latex",
    DocumentFormat.EPUB: "epub",
    DocumentFormat.TEXT: "plain",
}


def normalize_format(value: str) -> DocumentFormat:
    key = value.strip().lower().lstrip(".")
    try:
        return FORMAT_ALIASES[key]
    except KeyError as exc:
        raise ValueError(f"Unsupported format: {value}") from exc


def detect_format(path: Path) -> DocumentFormat:
    suffix = path.suffix.lower().lstrip(".")
    if not suffix:
        raise ValueError(f"Cannot infer format from path without extension: {path}")
    return normalize_format(suffix)


@dataclass(slots=True)
class ToolAvailability:
    name: str
    available: bool
    detail: str
    version: str | None = None


@dataclass(slots=True)
class TableData:
    name: str | None
    rows: list[dict[str, Any]]

    def to_markdown(self) -> str:
        if not self.rows:
            return ""
        headers: list[str] = []
        for row in self.rows:
            for key in row.keys():
                if key not in headers:
                    headers.append(key)
        header_line = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        body = []
        for row in self.rows:
            values = [str(row.get(header, "")) for header in headers]
            body.append("| " + " | ".join(values) + " |")
        return "\n".join([header_line, separator, *body])


@dataclass(slots=True)
class DocumentIR:
    source_path: Path
    source_format: DocumentFormat
    markdown: str | None = None
    plain_text: str | None = None
    html: str | None = None
    latex: str | None = None
    tables: list[TableData] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def markdown_text(self) -> str:
        if self.markdown:
            return self.markdown
        if self.tables:
            return "\n\n".join(table.to_markdown() for table in self.tables if table.rows)
        if self.plain_text:
            return self.plain_text
        if self.html:
            return self.html
        return ""

    def plain_text_value(self) -> str:
        if self.plain_text:
            return self.plain_text
        return self.markdown_text()

    def as_jsonable(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "source_format": self.source_format.value,
            "markdown": self.markdown,
            "plain_text": self.plain_text,
            "html": self.html,
            "latex": self.latex,
            "tables": [
                {
                    "name": table.name,
                    "rows": table.rows,
                }
                for table in self.tables
            ],
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ConversionRequest:
    input_path: Path
    output_path: Path
    source_format: DocumentFormat
    target_format: DocumentFormat
    force_ocr: bool = False
    prefer_engine: str | None = None


@dataclass(slots=True)
class PlanStep:
    engine: str
    action: str
    detail: str


@dataclass(slots=True)
class ConversionPlan:
    route_name: str
    score: int
    steps: list[PlanStep]
    direct_engine: str | None = None
    extractor: str | None = None
    renderer: str | None = None
    notes: list[str] = field(default_factory=list)

    def uses_engine(self, engine_name: str) -> bool:
        names = {self.direct_engine, self.extractor, self.renderer}
        return engine_name in names
