"""Format definitions, extension mapping, and MIME type registry."""

from enum import Enum


class DocFormat(str, Enum):
    """Supported document formats for conversion."""

    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"
    PLAIN_TEXT = "txt"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    LATEX = "latex"
    EPUB = "epub"
    RTF = "rtf"

    def __str__(self) -> str:
        return self.value


# File extension → DocFormat mapping (multiple extensions per format)
EXTENSION_MAP: dict[str, DocFormat] = {
    ".pdf": DocFormat.PDF,
    ".docx": DocFormat.DOCX,
    ".md": DocFormat.MARKDOWN,
    ".markdown": DocFormat.MARKDOWN,
    ".txt": DocFormat.PLAIN_TEXT,
    ".text": DocFormat.PLAIN_TEXT,
    ".html": DocFormat.HTML,
    ".htm": DocFormat.HTML,
    ".json": DocFormat.JSON,
    ".csv": DocFormat.CSV,
    ".tex": DocFormat.LATEX,
    ".latex": DocFormat.LATEX,
    ".epub": DocFormat.EPUB,
    ".rtf": DocFormat.RTF,
}

# DocFormat → canonical file extension
FORMAT_EXTENSION: dict[DocFormat, str] = {
    DocFormat.PDF: ".pdf",
    DocFormat.DOCX: ".docx",
    DocFormat.MARKDOWN: ".md",
    DocFormat.PLAIN_TEXT: ".txt",
    DocFormat.HTML: ".html",
    DocFormat.JSON: ".json",
    DocFormat.CSV: ".csv",
    DocFormat.LATEX: ".tex",
    DocFormat.EPUB: ".epub",
    DocFormat.RTF: ".rtf",
}

# MIME type → DocFormat mapping for python-magic detection
MIME_MAP: dict[str, DocFormat] = {
    "application/pdf": DocFormat.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocFormat.DOCX,
    "text/markdown": DocFormat.MARKDOWN,
    "text/plain": DocFormat.PLAIN_TEXT,
    "text/html": DocFormat.HTML,
    "application/json": DocFormat.JSON,
    "text/csv": DocFormat.CSV,
    "text/x-tex": DocFormat.LATEX,
    "application/x-tex": DocFormat.LATEX,
    "application/epub+zip": DocFormat.EPUB,
    "text/rtf": DocFormat.RTF,
    "application/rtf": DocFormat.RTF,
}

# Pandoc format identifiers for pypandoc calls
PANDOC_FORMAT_MAP: dict[DocFormat, str] = {
    DocFormat.PDF: "pdf",
    DocFormat.DOCX: "docx",
    DocFormat.MARKDOWN: "markdown",
    DocFormat.PLAIN_TEXT: "plain",
    DocFormat.HTML: "html",
    DocFormat.JSON: "json",
    DocFormat.CSV: "csv",
    DocFormat.LATEX: "latex",
    DocFormat.EPUB: "epub",
    DocFormat.RTF: "rtf",
}


def format_from_string(s: str) -> DocFormat:
    """Parse a format string like 'pdf', 'md', 'docx' into a DocFormat enum.

    Args:
        s: Format string (case-insensitive).

    Returns:
        Matching DocFormat enum value.

    Raises:
        ValueError: If the string doesn't match any known format.
    """
    s_lower = s.lower().strip().lstrip(".")
    # Direct enum value match
    for fmt in DocFormat:
        if fmt.value == s_lower:
            return fmt
    # Extension map match
    for ext, fmt in EXTENSION_MAP.items():
        if ext.lstrip(".") == s_lower:
            return fmt
    raise ValueError(
        f"Unknown format: '{s}'. Supported: {', '.join(f.value for f in DocFormat)}"
    )
