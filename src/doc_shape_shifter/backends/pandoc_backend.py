"""Pandoc backend — the universal document format bridge."""

import logging
import shutil
import subprocess
import time
from pathlib import Path

from .base import BaseBackend, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.pandoc")

_PANDOC_FORMATS = {
    "pdf": "pdf",
    "docx": "docx",
    "md": "markdown",
    "txt": "plain",
    "html": "html",
    "json": "json",
    "csv": "csv",
    "latex": "latex",
    "epub": "epub",
    "rtf": "rtf",
}


class PandocBackend(BaseBackend):
    """Backend using Pandoc for broad format conversion."""

    name = "pandoc"

    def is_available(self) -> bool:
        if shutil.which("pandoc") is not None:
            return True
        try:
            import pypandoc  # noqa: F401
            return True
        except ImportError:
            return False

    def version_info(self) -> str:
        pandoc_path = shutil.which("pandoc")
        if pandoc_path:
            try:
                result = subprocess.run(
                    ["pandoc", "--version"], capture_output=True, text=True, timeout=5
                )
                first_line = result.stdout.strip().split("\n")[0]
                return first_line
            except Exception:
                return "pandoc (version unknown)"

        try:
            import pypandoc
            return f"pypandoc {pypandoc.__version__}"
        except (ImportError, AttributeError):
            return "pandoc (not installed)"

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        start = time.time()
        logger.info(
            "pandoc: converting %s -> %s (%s)",
            source_format, target_format, input_path.name,
        )

        pandoc_from = _PANDOC_FORMATS.get(source_format)
        pandoc_to = _PANDOC_FORMATS.get(target_format)

        # "plain" is only a pandoc output format, not input.
        # For plain text input, omit -f and let pandoc auto-detect.
        if pandoc_from == "plain":
            pandoc_from = None

        if pandoc_to is None:
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=time.time() - start,
                source_format=source_format, target_format=target_format,
                error_message=(
                    f"Pandoc format mapping missing: "
                    f"{source_format}={pandoc_from}, {target_format}={pandoc_to}"
                ),
            )

        try:
            converted = self._try_pypandoc(input_path, output_path, pandoc_from, pandoc_to)
            if not converted:
                self._run_cli(input_path, output_path, pandoc_from, pandoc_to)

            duration = time.time() - start
            size = output_path.stat().st_size if output_path.exists() else None

            logger.info(
                "pandoc: conversion complete in %.2fs (%s bytes)",
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
            logger.error("pandoc: conversion failed: %s", e, exc_info=True)
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=str(e),
            )

    def _try_pypandoc(
        self, input_path: Path, output_path: Path,
        pandoc_from: str | None, pandoc_to: str,
    ) -> bool:
        """Attempt conversion using pypandoc. Returns True if successful."""
        try:
            import pypandoc
            kwargs = {
                "outputfile": str(output_path),
            }
            if pandoc_from:
                kwargs["format"] = pandoc_from
            pypandoc.convert_file(
                str(input_path),
                pandoc_to,
                **kwargs,
            )
            logger.debug("pandoc: used pypandoc library")
            return True
        except ImportError:
            logger.debug("pandoc: pypandoc not installed, falling back to CLI")
            return False

    def _run_cli(
        self, input_path: Path, output_path: Path,
        pandoc_from: str | None, pandoc_to: str,
    ) -> None:
        """Run pandoc as a subprocess."""
        cmd = [
            "pandoc",
            str(input_path),
        ]
        if pandoc_from:
            cmd.extend(["-f", pandoc_from])
        cmd.extend([
            "-t", pandoc_to,
            "-o", str(output_path),
            "--standalone",
        ])
        logger.debug("pandoc CLI: %s", " ".join(cmd))

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            error = result.stderr.strip() or f"pandoc exited with code {result.returncode}"
            raise RuntimeError(f"Pandoc CLI error: {error}")
