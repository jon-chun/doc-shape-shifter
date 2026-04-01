"""Conversion matrix and backend selection logic.

Maps each (source_format, target_format) pair to an ordered list of backend names.
The first available backend in the list is used; subsequent entries are fallbacks.
"""

import logging

from .utils.formats import DocFormat

logger = logging.getLogger("doc_shape_shifter.router")


class UnsupportedConversionError(Exception):
    """Raised when no conversion path exists between two formats."""


# ============================================================================
# CONVERSION MATRIX
# Each value is an ordered list of backend names (best -> fallback).
# ============================================================================

CONVERSION_MATRIX: dict[tuple[DocFormat, DocFormat], list[str]] = {
    # --- PDF (native) as source ---
    (DocFormat.PDF, DocFormat.DOCX):       ["pandoc", "docling"],
    (DocFormat.PDF, DocFormat.MARKDOWN):    ["docling", "pymupdf", "pandoc", "markitdown"],
    (DocFormat.PDF, DocFormat.PLAIN_TEXT):  ["pymupdf", "docling", "pandoc"],
    (DocFormat.PDF, DocFormat.HTML):        ["docling", "pandoc"],
    (DocFormat.PDF, DocFormat.JSON):        ["docling"],
    (DocFormat.PDF, DocFormat.CSV):         ["tabula"],
    (DocFormat.PDF, DocFormat.LATEX):       ["mathpix", "pandoc"],
    (DocFormat.PDF, DocFormat.EPUB):        ["pandoc"],
    (DocFormat.PDF, DocFormat.RTF):         ["pandoc"],

    # --- DOCX as source ---
    (DocFormat.DOCX, DocFormat.PDF):        ["pandoc"],
    (DocFormat.DOCX, DocFormat.MARKDOWN):   ["markitdown", "docling", "pandoc"],
    (DocFormat.DOCX, DocFormat.PLAIN_TEXT):  ["docling", "markitdown", "pandoc"],
    (DocFormat.DOCX, DocFormat.HTML):       ["docling", "pandoc"],
    (DocFormat.DOCX, DocFormat.JSON):       ["markitdown", "docling"],
    (DocFormat.DOCX, DocFormat.LATEX):      ["pandoc"],
    (DocFormat.DOCX, DocFormat.EPUB):       ["pandoc"],
    (DocFormat.DOCX, DocFormat.RTF):        ["pandoc"],

    # --- Markdown as source ---
    (DocFormat.MARKDOWN, DocFormat.PDF):        ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.DOCX):       ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.PLAIN_TEXT):  ["builtin"],
    (DocFormat.MARKDOWN, DocFormat.HTML):        ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.JSON):        ["markitdown", "builtin"],
    (DocFormat.MARKDOWN, DocFormat.LATEX):       ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.EPUB):        ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.RTF):         ["pandoc"],
    (DocFormat.MARKDOWN, DocFormat.CSV):         [],  # Not meaningful

    # --- Plain Text as source ---
    (DocFormat.PLAIN_TEXT, DocFormat.PDF):        ["pandoc"],
    (DocFormat.PLAIN_TEXT, DocFormat.DOCX):       ["pandoc"],
    (DocFormat.PLAIN_TEXT, DocFormat.MARKDOWN):   ["builtin"],
    (DocFormat.PLAIN_TEXT, DocFormat.HTML):        ["pandoc"],
    (DocFormat.PLAIN_TEXT, DocFormat.LATEX):       ["pandoc"],
    (DocFormat.PLAIN_TEXT, DocFormat.RTF):         ["pandoc"],

    # --- HTML as source ---
    (DocFormat.HTML, DocFormat.PDF):        ["pandoc"],
    (DocFormat.HTML, DocFormat.DOCX):       ["pandoc"],
    (DocFormat.HTML, DocFormat.MARKDOWN):   ["docling", "pandoc"],
    (DocFormat.HTML, DocFormat.PLAIN_TEXT):  ["builtin", "pandoc"],
    (DocFormat.HTML, DocFormat.JSON):       ["docling"],
    (DocFormat.HTML, DocFormat.CSV):        ["builtin"],
    (DocFormat.HTML, DocFormat.LATEX):      ["pandoc"],
    (DocFormat.HTML, DocFormat.EPUB):       ["pandoc"],
    (DocFormat.HTML, DocFormat.RTF):        ["pandoc"],

    # --- JSON as source ---
    (DocFormat.JSON, DocFormat.MARKDOWN):   ["markitdown"],
    (DocFormat.JSON, DocFormat.PLAIN_TEXT):  ["builtin"],
    (DocFormat.JSON, DocFormat.HTML):       ["docling"],
    (DocFormat.JSON, DocFormat.CSV):        ["builtin"],

    # --- CSV as source ---
    (DocFormat.CSV, DocFormat.MARKDOWN):    ["markitdown"],
    (DocFormat.CSV, DocFormat.PLAIN_TEXT):  ["builtin"],
    (DocFormat.CSV, DocFormat.JSON):        ["builtin"],
    (DocFormat.CSV, DocFormat.HTML):        ["pandoc"],

    # --- LaTeX as source ---
    (DocFormat.LATEX, DocFormat.PDF):       ["pandoc"],
    (DocFormat.LATEX, DocFormat.DOCX):      ["pandoc"],
    (DocFormat.LATEX, DocFormat.MARKDOWN):  ["docling", "pandoc"],
    (DocFormat.LATEX, DocFormat.PLAIN_TEXT): ["pandoc"],
    (DocFormat.LATEX, DocFormat.HTML):      ["pandoc"],
    (DocFormat.LATEX, DocFormat.EPUB):      ["pandoc"],

    # --- EPUB as source ---
    (DocFormat.EPUB, DocFormat.PDF):        ["pandoc"],
    (DocFormat.EPUB, DocFormat.DOCX):       ["pandoc"],
    (DocFormat.EPUB, DocFormat.MARKDOWN):   ["markitdown", "pandoc"],
    (DocFormat.EPUB, DocFormat.PLAIN_TEXT):  ["markitdown", "pandoc"],
    (DocFormat.EPUB, DocFormat.HTML):       ["pandoc"],

    # --- RTF as source ---
    (DocFormat.RTF, DocFormat.PDF):         ["pandoc"],
    (DocFormat.RTF, DocFormat.DOCX):        ["pandoc"],
    (DocFormat.RTF, DocFormat.MARKDOWN):    ["markitdown", "pandoc"],
    (DocFormat.RTF, DocFormat.PLAIN_TEXT):   ["markitdown", "pandoc"],
    (DocFormat.RTF, DocFormat.HTML):        ["pandoc"],
    (DocFormat.RTF, DocFormat.JSON):        ["markitdown"],
}


def get_backend_chain(source: DocFormat, target: DocFormat) -> list[str]:
    """Return the ordered list of backend names for a given conversion pair."""
    if source == target:
        raise UnsupportedConversionError(
            f"Source and target formats are the same: {source}"
        )

    chain = CONVERSION_MATRIX.get((source, target))

    if chain is None or len(chain) == 0:
        raise UnsupportedConversionError(
            f"No conversion path from {source.value} -> {target.value}. "
            f"This conversion may be semantically lossy or not yet supported."
        )

    logger.debug(
        "Backend chain for %s -> %s: %s",
        source.value, target.value, " -> ".join(chain),
    )
    return chain


def get_best_available_backend(source: DocFormat, target: DocFormat) -> str | None:
    """Return the first installed backend for a conversion pair."""
    from .backends import get_backend

    try:
        chain = get_backend_chain(source, target)
    except UnsupportedConversionError:
        return None

    for name in chain:
        try:
            backend = get_backend(name)
            if backend.is_available():
                logger.debug("Best available backend for %s -> %s: %s", source, target, name)
                return name
        except KeyError:
            logger.warning("Unknown backend in chain: %s", name)
            continue

    logger.warning("No available backend for %s -> %s", source, target)
    return None


def list_supported_conversions() -> list[tuple[str, str, list[str]]]:
    """List all defined conversion pairs with their backend chains."""
    results = []
    for (src, tgt), chain in sorted(
        CONVERSION_MATRIX.items(), key=lambda x: (x[0][0].value, x[0][1].value)
    ):
        if chain:
            results.append((src.value, tgt.value, chain))
    return results
