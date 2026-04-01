"""Main orchestration module: detect -> route -> convert with fallback chain."""

import logging
import time
from pathlib import Path

from .backends import get_backend
from .backends.base import ConversionResult
from .detector import detect_format
from .router import UnsupportedConversionError, get_backend_chain
from .utils.formats import FORMAT_EXTENSION, DocFormat, format_from_string

logger = logging.getLogger("doc_shape_shifter.converter")


def convert(
    input_path: str | Path,
    output_path: str | Path | None = None,
    target_format: str | None = None,
    backend: str | None = None,
    fallback: bool = True,
) -> ConversionResult:
    """Convert a document from one format to another.

    Workflow:
        1. Detect source format from input file
        2. Determine target format (from output_path extension or target_format arg)
        3. Look up backend chain from the conversion matrix
        4. Execute first available backend (or forced backend if specified)
        5. On failure, try next backend in chain if fallback=True
        6. Return ConversionResult with full metadata
    """
    overall_start = time.time()
    input_path = Path(input_path)

    # --- Step 1: Detect source format ---
    logger.info("=" * 60)
    logger.info("Starting conversion: %s", input_path.name)
    source_fmt = detect_format(input_path)
    logger.info("Source format detected: %s", source_fmt.value)

    # --- Step 2: Determine target format ---
    target_fmt = _resolve_target_format(output_path, target_format)
    logger.info("Target format: %s", target_fmt.value)

    # --- Step 3: Resolve output path ---
    if output_path is None:
        ext = FORMAT_EXTENSION[target_fmt]
        output_path = input_path.with_suffix(ext)
    output_path = Path(output_path)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Output path: %s", output_path)
    logger.info(
        "Conversion: %s -> %s",
        source_fmt.value, target_fmt.value,
        extra={
            "source_format": source_fmt.value,
            "target_format": target_fmt.value,
            "input_file": str(input_path),
            "output_file": str(output_path),
        },
    )

    # --- Step 4: Get backend chain ---
    try:
        if backend:
            chain = [backend]
            logger.info("Using forced backend: %s", backend)
        else:
            chain = get_backend_chain(source_fmt, target_fmt)
            logger.info("Backend chain: %s", " -> ".join(chain))
    except UnsupportedConversionError as e:
        duration = time.time() - overall_start
        logger.error("No conversion path: %s", e)
        return ConversionResult(
            success=False,
            output_path=None,
            backend_name="none",
            duration_seconds=duration,
            source_format=source_fmt.value,
            target_format=target_fmt.value,
            error_message=str(e),
        )

    # --- Step 5: Execute conversion with fallback ---
    errors: list[str] = []

    for i, backend_name in enumerate(chain):
        progress = f"[{i + 1}/{len(chain)}]"

        try:
            be = get_backend(backend_name)
        except KeyError as e:
            logger.warning("%s Unknown backend '%s': %s", progress, backend_name, e)
            errors.append(f"{backend_name}: unknown backend")
            continue

        if not be.is_available():
            logger.warning(
                "%s Backend '%s' not available (not installed)",
                progress, backend_name,
            )
            errors.append(f"{backend_name}: not installed")
            if not fallback:
                break
            continue

        logger.info("%s Trying backend: %s (%s)", progress, backend_name, be.version_info())
        result = be.convert(input_path, output_path, source_fmt.value, target_fmt.value)

        if result.success:
            logger.info(
                "Conversion SUCCESS via %s in %.2fs",
                backend_name, result.duration_seconds,
            )
            result.duration_seconds = time.time() - overall_start
            return result

        logger.warning(
            "%s Backend '%s' failed: %s",
            progress, backend_name, result.error_message,
        )
        errors.append(f"{backend_name}: {result.error_message}")

        if not fallback:
            logger.info("Fallback disabled, stopping after first failure")
            break

    # --- All backends exhausted ---
    duration = time.time() - overall_start
    error_summary = "; ".join(errors) if errors else "No backends available"
    logger.error(
        "Conversion FAILED: all %d backends exhausted for %s -> %s. Errors: %s",
        len(chain), source_fmt.value, target_fmt.value, error_summary,
    )

    return ConversionResult(
        success=False,
        output_path=None,
        backend_name="none",
        duration_seconds=duration,
        source_format=source_fmt.value,
        target_format=target_fmt.value,
        error_message=f"All backends failed: {error_summary}",
    )


def _resolve_target_format(
    output_path: str | Path | None,
    target_format: str | None,
) -> DocFormat:
    """Determine the target format from output path and/or explicit format string."""
    if target_format:
        return format_from_string(target_format)

    if output_path:
        from .utils.formats import EXTENSION_MAP
        ext = Path(output_path).suffix.lower()
        fmt = EXTENSION_MAP.get(ext)
        if fmt:
            return fmt
        raise ValueError(
            f"Cannot determine target format from extension '{ext}'. "
            f"Use --to to specify the format explicitly."
        )

    raise ValueError(
        "Target format is required. Specify via output file extension or --to flag."
    )
