"""Time estimation for conversions based on format pair, backend, and file size."""

from __future__ import annotations

import os
from pathlib import Path

# Base times in seconds for a ~10 KB file on each backend.
# Keyed by (backend_name, source_format, target_format) where applicable,
# with broader fallbacks by backend name.
#
# These are conservative estimates; actual times are logged and could feed
# a calibration system in future.

_BASE_TIMES: dict[tuple[str, str, str], float] = {
    # builtin — pure Python, near-instant
    ("builtin", "md", "txt"): 0.05,
    ("builtin", "html", "txt"): 0.05,
    ("builtin", "json", "csv"): 0.05,
    ("builtin", "csv", "json"): 0.05,
    ("builtin", "json", "txt"): 0.05,
    ("builtin", "txt", "md"): 0.02,
    ("builtin", "html", "csv"): 0.08,
    ("builtin", "csv", "txt"): 0.03,
    # pandoc — subprocess, moderate
    ("pandoc", "md", "html"): 0.3,
    ("pandoc", "md", "docx"): 0.5,
    ("pandoc", "md", "pdf"): 2.0,
    ("pandoc", "md", "latex"): 0.4,
    ("pandoc", "md", "epub"): 1.0,
    ("pandoc", "md", "rtf"): 0.4,
    ("pandoc", "html", "md"): 0.3,
    ("pandoc", "html", "docx"): 0.5,
    ("pandoc", "html", "pdf"): 2.0,
    ("pandoc", "html", "epub"): 1.0,
    ("pandoc", "html", "latex"): 0.4,
    ("pandoc", "html", "rtf"): 0.4,
    ("pandoc", "latex", "html"): 0.5,
    ("pandoc", "latex", "md"): 0.4,
    ("pandoc", "latex", "docx"): 0.6,
    ("pandoc", "latex", "pdf"): 3.0,
    ("pandoc", "latex", "epub"): 1.2,
    ("pandoc", "txt", "html"): 0.3,
    ("pandoc", "txt", "docx"): 0.4,
    ("pandoc", "txt", "pdf"): 1.5,
    ("pandoc", "txt", "latex"): 0.3,
    ("pandoc", "txt", "rtf"): 0.3,
    ("pandoc", "csv", "html"): 0.3,
    ("pandoc", "epub", "html"): 0.5,
    ("pandoc", "epub", "md"): 0.5,
    ("pandoc", "epub", "docx"): 0.7,
    ("pandoc", "epub", "pdf"): 2.5,
    ("pandoc", "rtf", "html"): 0.4,
    ("pandoc", "rtf", "md"): 0.4,
    ("pandoc", "rtf", "docx"): 0.5,
    ("pandoc", "rtf", "pdf"): 2.0,
    ("pandoc", "docx", "pdf"): 2.0,
    ("pandoc", "docx", "html"): 0.5,
    ("pandoc", "docx", "md"): 0.5,
    ("pandoc", "docx", "latex"): 0.5,
    ("pandoc", "docx", "epub"): 1.0,
    ("pandoc", "docx", "rtf"): 0.4,
    # pymupdf — fast native C library
    ("pymupdf", "pdf", "txt"): 0.2,
    ("pymupdf", "pdf", "md"): 0.3,
    # docling — AI model, heavier
    ("docling", "pdf", "md"): 5.0,
    ("docling", "pdf", "json"): 5.0,
    ("docling", "pdf", "html"): 5.0,
    ("docling", "pdf", "txt"): 5.0,
    ("docling", "docx", "md"): 3.0,
    ("docling", "docx", "txt"): 3.0,
    ("docling", "docx", "html"): 3.0,
    ("docling", "docx", "json"): 3.0,
    ("docling", "html", "md"): 2.0,
    ("docling", "html", "json"): 2.0,
    ("docling", "latex", "md"): 3.0,
    # markitdown — lightweight
    ("markitdown", "docx", "md"): 0.5,
    ("markitdown", "docx", "txt"): 0.5,
    ("markitdown", "docx", "json"): 0.5,
    ("markitdown", "epub", "md"): 0.8,
    ("markitdown", "epub", "txt"): 0.8,
    ("markitdown", "rtf", "md"): 0.4,
    ("markitdown", "rtf", "txt"): 0.4,
    ("markitdown", "rtf", "json"): 0.4,
    ("markitdown", "csv", "md"): 0.2,
    ("markitdown", "json", "md"): 0.2,
    ("markitdown", "md", "json"): 0.2,
    # tabula — Java subprocess, slow startup
    ("tabula", "pdf", "csv"): 3.0,
    ("tabula", "pdf", "json"): 3.0,
    # mathpix — network API, very slow
    ("mathpix", "pdf", "latex"): 30.0,
}

# Fallback base times by backend when no specific triple exists
_BACKEND_DEFAULTS: dict[str, float] = {
    "builtin": 0.05,
    "pandoc": 0.5,
    "pymupdf": 0.3,
    "docling": 5.0,
    "markitdown": 0.5,
    "tabula": 3.0,
    "mathpix": 30.0,
}

# Size scaling: seconds per MB beyond the base 10 KB reference.
# Different backends scale differently with file size.
_SIZE_SCALE_PER_MB: dict[str, float] = {
    "builtin": 0.1,
    "pandoc": 0.5,
    "pymupdf": 0.2,
    "docling": 8.0,
    "markitdown": 0.5,
    "tabula": 2.0,
    "mathpix": 10.0,
}

_DEFAULT_SCALE_PER_MB = 1.0


def estimate_conversion_time(
    backend_name: str,
    source_format: str,
    target_format: str,
    file_size_bytes: int | None = None,
) -> float:
    """Estimate conversion time in seconds.

    Args:
        backend_name: Name of the backend that will perform conversion.
        source_format: Source format string (e.g. "pdf", "md").
        target_format: Target format string (e.g. "docx", "txt").
        file_size_bytes: Size of the input file in bytes. If None, returns
            the base estimate for a small file.

    Returns:
        Estimated seconds as a float.
    """
    base = _BASE_TIMES.get(
        (backend_name, source_format, target_format),
        _BACKEND_DEFAULTS.get(backend_name, 1.0),
    )

    if file_size_bytes is None or file_size_bytes <= 10240:
        return base

    # Scale linearly beyond 10 KB reference point
    extra_mb = (file_size_bytes - 10240) / (1024 * 1024)
    scale = _SIZE_SCALE_PER_MB.get(backend_name, _DEFAULT_SCALE_PER_MB)
    return base + extra_mb * scale


def estimate_for_file(
    backend_name: str,
    source_format: str,
    target_format: str,
    input_path: Path | str,
) -> float:
    """Estimate conversion time for a specific file on disk.

    Args:
        backend_name: Backend name.
        source_format: Source format string.
        target_format: Target format string.
        input_path: Path to the input file.

    Returns:
        Estimated seconds. Returns base estimate if file cannot be stat'd.
    """
    try:
        size = os.path.getsize(input_path)
    except OSError:
        size = None
    return estimate_conversion_time(backend_name, source_format, target_format, size)


def format_eta(seconds: float) -> str:
    """Format an ETA in seconds into a human-readable string.

    Examples:
        0.3  -> "<1s"
        5.0  -> "~5s"
        65.0 -> "~1m 5s"
        125  -> "~2m 5s"
    """
    if seconds < 1.0:
        return "<1s"
    if seconds < 60.0:
        return f"~{seconds:.0f}s"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    if secs == 0:
        return f"~{minutes}m"
    return f"~{minutes}m {secs}s"
