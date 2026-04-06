"""Format detection using MIME types, file extensions, and content heuristics."""

import logging
from pathlib import Path

from .utils.formats import DocFormat, EXTENSION_MAP, MIME_MAP

logger = logging.getLogger("doc_shape_shifter.detector")


class UnsupportedFormatError(Exception):
    """Raised when a file's format cannot be detected or is not supported."""


def _detect_by_magic(file_path: Path) -> DocFormat | None:
    """Attempt MIME-type detection via python-magic."""
    try:
        import magic

        mime_type = magic.from_file(str(file_path), mime=True)
        logger.debug("python-magic detected MIME: %s for %s", mime_type, file_path.name)
        result = MIME_MAP.get(mime_type)
        if result:
            return result

        # Some MIME types are ambiguous — text/plain could be .md, .csv, .tex, .txt
        # Fall through to extension/heuristic detection
        if mime_type == "text/plain":
            logger.debug("MIME is text/plain, deferring to extension/heuristic detection")
            return None

        logger.debug("MIME type '%s' not in known map", mime_type)
        return None

    except ImportError:
        logger.debug("python-magic not installed, skipping MIME detection")
        return None
    except Exception as e:
        logger.debug("python-magic error: %s", e)
        return None


def _detect_by_extension(file_path: Path) -> DocFormat | None:
    """Detect format from file extension."""
    ext = file_path.suffix.lower()
    result = EXTENSION_MAP.get(ext)
    if result:
        logger.debug("Extension '%s' maps to format: %s", ext, result)
    else:
        logger.debug("Extension '%s' not in known map", ext)
    return result


def _detect_by_heuristic(file_path: Path) -> DocFormat | None:
    """Detect format by inspecting file content headers/patterns."""
    try:
        # Read first 4096 bytes for heuristic analysis
        with open(file_path, "rb") as f:
            header = f.read(4096)

        # PDF: starts with %PDF-
        if header.startswith(b"%PDF-"):
            logger.debug("Heuristic: PDF header detected")
            return DocFormat.PDF

        # EPUB: ZIP with mimetype entry
        if header[:4] == b"PK\x03\x04" and b"mimetype" in header[:100]:
            logger.debug("Heuristic: EPUB (ZIP with mimetype) detected")
            return DocFormat.EPUB

        # DOCX: ZIP with word/ directory
        if header[:4] == b"PK\x03\x04" and (b"word/" in header or b"[Content_Types]" in header):
            logger.debug("Heuristic: DOCX (ZIP with word/) detected")
            return DocFormat.DOCX

        # Try text-based heuristics
        try:
            text_sample = header.decode("utf-8", errors="ignore")
        except Exception:
            return None

        # LaTeX: \documentclass or \begin{document}
        if "\\documentclass" in text_sample or "\\begin{document}" in text_sample:
            logger.debug("Heuristic: LaTeX markers detected")
            return DocFormat.LATEX

        # HTML: doctype or html tags
        text_lower = text_sample.lower()
        if "<!doctype html" in text_lower or "<html" in text_lower:
            logger.debug("Heuristic: HTML markers detected")
            return DocFormat.HTML

        # JSON: starts with { or [
        stripped = text_sample.strip()
        if stripped and stripped[0] in "{[":
            try:
                import json

                json.loads(file_path.read_text(encoding="utf-8"))
                logger.debug("Heuristic: Valid JSON detected")
                return DocFormat.JSON
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # CSV: check for comma-separated structure in first few lines
        lines = text_sample.strip().split("\n")[:5]
        if len(lines) >= 2:
            comma_counts = [line.count(",") for line in lines]
            if all(c > 0 for c in comma_counts) and len(set(comma_counts)) <= 2:
                logger.debug("Heuristic: CSV structure detected")
                return DocFormat.CSV

        # RTF: {\rtf
        if text_sample.startswith("{\\rtf"):
            logger.debug("Heuristic: RTF header detected")
            return DocFormat.RTF

        # Markdown: check for markdown-specific patterns
        md_indicators = 0
        if text_sample.startswith("# ") or "\n# " in text_sample:
            md_indicators += 1
        if "```" in text_sample:
            md_indicators += 1
        if "[" in text_sample and "](" in text_sample:
            md_indicators += 1
        if md_indicators >= 2:
            logger.debug("Heuristic: Markdown patterns detected (%d indicators)", md_indicators)
            return DocFormat.MARKDOWN

    except Exception as e:
        logger.debug("Heuristic detection error: %s", e)

    return None


def detect_format(file_path: Path | str) -> DocFormat:
    """Detect the document format of a file using layered detection.

    Detection order:
        1. python-magic MIME type (most reliable for binary formats)
        2. File extension (fast, usually correct)
        3. Content heuristics (fallback for ambiguous cases)

    Args:
        file_path: Path to the input file.

    Returns:
        Detected DocFormat.

    Raises:
        UnsupportedFormatError: If format cannot be determined.
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info("Detecting format for: %s", file_path.name)

    # Layer 1: MIME type
    result = _detect_by_magic(file_path)
    if result:
        logger.info("Format detected via MIME: %s", result)
        return result

    # Layer 2: Extension
    result = _detect_by_extension(file_path)
    if result:
        logger.info("Format detected via extension: %s", result)
        return result

    # Layer 3: Content heuristics
    result = _detect_by_heuristic(file_path)
    if result:
        logger.info("Format detected via heuristic: %s", result)
        return result

    raise UnsupportedFormatError(
        f"Cannot detect format for '{file_path.name}'. "
        f"Supported extensions: {', '.join(sorted(EXTENSION_MAP.keys()))}"
    )
