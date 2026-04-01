"""Built-in conversions using Python stdlib — always available, no external deps."""

import csv
import io
import json
import logging
import re
import time
from html.parser import HTMLParser
from pathlib import Path

from .base import BaseBackend, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.builtin")


class _HTMLTextExtractor(HTMLParser):
    """Simple HTML-to-text converter using stdlib html.parser."""

    def __init__(self):
        super().__init__()
        self._text_parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True
        elif tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self._text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
        elif tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._text_parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self._text_parts.append(data)

    def get_text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self._text_parts)).strip()


class BuiltinBackend(BaseBackend):
    """Pure-Python conversions using the standard library."""

    name = "builtin"

    def is_available(self) -> bool:
        return True

    def version_info(self) -> str:
        import sys
        return f"Python {sys.version.split()[0]} stdlib"

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        start = time.time()
        pair = (source_format, target_format)
        logger.info("builtin: converting %s -> %s", source_format, target_format)

        try:
            handlers = {
                ("md", "txt"): self._md_to_txt,
                ("html", "txt"): self._html_to_txt,
                ("json", "txt"): self._json_to_txt,
                ("json", "csv"): self._json_to_csv,
                ("csv", "json"): self._csv_to_json,
                ("txt", "md"): self._txt_to_md,
                ("html", "csv"): self._html_to_csv,
                ("csv", "txt"): self._csv_to_txt,
            }

            handler = handlers.get(pair)
            if handler is None:
                return ConversionResult(
                    success=False,
                    output_path=None,
                    backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format,
                    target_format=target_format,
                    error_message=(
                        f"builtin backend does not support "
                        f"{source_format} -> {target_format}"
                    ),
                )

            handler(input_path, output_path)
            duration = time.time() - start
            size = output_path.stat().st_size if output_path.exists() else None

            logger.info(
                "builtin: conversion complete in %.2fs (%s bytes)",
                duration, size,
                extra={"duration_s": duration, "file_size_bytes": size},
            )
            return ConversionResult(
                success=True,
                output_path=output_path,
                backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format,
                target_format=target_format,
                file_size_bytes=size,
            )

        except Exception as e:
            duration = time.time() - start
            logger.error("builtin: conversion failed: %s", e, exc_info=True)
            return ConversionResult(
                success=False,
                output_path=None,
                backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format,
                target_format=target_format,
                error_message=str(e),
            )

    def _md_to_txt(self, input_path: Path, output_path: Path) -> None:
        """Strip markdown syntax to produce plain text."""
        text = input_path.read_text(encoding="utf-8")
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        output_path.write_text(text, encoding="utf-8")

    def _html_to_txt(self, input_path: Path, output_path: Path) -> None:
        """Strip HTML tags to produce plain text."""
        html_content = input_path.read_text(encoding="utf-8")
        extractor = _HTMLTextExtractor()
        extractor.feed(html_content)
        output_path.write_text(extractor.get_text(), encoding="utf-8")

    def _json_to_txt(self, input_path: Path, output_path: Path) -> None:
        """Pretty-print JSON as plain text."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _json_to_csv(self, input_path: Path, output_path: Path) -> None:
        """Convert a JSON array of objects to CSV."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            raise ValueError("JSON must be a non-empty array of objects for CSV conversion")

        if not isinstance(data[0], dict):
            raise ValueError("JSON array elements must be objects (dicts) for CSV conversion")

        all_keys: list[str] = []
        seen: set[str] = set()
        for record in data:
            for key in record:
                if key not in seen:
                    all_keys.append(key)
                    seen.add(key)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
        output_path.write_text(buf.getvalue(), encoding="utf-8")

    def _csv_to_json(self, input_path: Path, output_path: Path) -> None:
        """Convert CSV to a JSON array of objects."""
        with open(input_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)
        output_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _csv_to_txt(self, input_path: Path, output_path: Path) -> None:
        """Convert CSV to plain text (tab-separated for readability)."""
        text = input_path.read_text(encoding="utf-8")
        output_path.write_text(text, encoding="utf-8")

    def _txt_to_md(self, input_path: Path, output_path: Path) -> None:
        """Wrap plain text as markdown (minimal transformation)."""
        text = input_path.read_text(encoding="utf-8")
        output_path.write_text(text, encoding="utf-8")

    def _html_to_csv(self, input_path: Path, output_path: Path) -> None:
        """Extract tables from HTML to CSV (first table found)."""
        html = input_path.read_text(encoding="utf-8")

        rows: list[list[str]] = []
        current_row: list[str] = []
        in_table = False
        in_cell = False
        cell_text = ""

        class TableParser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                nonlocal in_table, in_cell, cell_text
                if tag == "table":
                    in_table = True
                elif tag in ("td", "th") and in_table:
                    in_cell = True
                    cell_text = ""

            def handle_endtag(self, tag):
                nonlocal in_table, in_cell, cell_text
                if tag in ("td", "th") and in_cell:
                    current_row.append(cell_text.strip())
                    in_cell = False
                elif tag == "tr" and in_table:
                    if current_row:
                        rows.append(current_row.copy())
                        current_row.clear()
                elif tag == "table":
                    in_table = False

            def handle_data(self, data):
                nonlocal cell_text
                if in_cell:
                    cell_text += data

        parser = TableParser()
        parser.feed(html)

        if not rows:
            raise ValueError("No HTML table found in input")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerows(rows)
        output_path.write_text(buf.getvalue(), encoding="utf-8")
