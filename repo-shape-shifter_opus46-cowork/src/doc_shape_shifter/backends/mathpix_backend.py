"""Mathpix backend — specialized PDF/image → LaTeX conversion (commercial API)."""

import logging
import os
import time
from pathlib import Path

from .base import BaseBackend, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.mathpix")


class MathpixBackend(BaseBackend):
    """Backend using Mathpix API for converting math-heavy documents to LaTeX.

    Strengths:
    - Industry leader for mathematical notation → LaTeX
    - Handles complex nested fractions, matrices, chemical formulas
    - High accuracy on scientific documents

    Limitations:
    - Requires API key (MATHPIX_APP_ID + MATHPIX_APP_KEY)
    - Commercial service with page limits
    - Network-dependent (not local-first)
    - Only supports PDF/image → LaTeX
    """

    name = "mathpix"

    def is_available(self) -> bool:
        app_id = os.environ.get("MATHPIX_APP_ID", "")
        app_key = os.environ.get("MATHPIX_APP_KEY", "")
        if not app_id or not app_key:
            logger.debug("mathpix: API credentials not set (MATHPIX_APP_ID, MATHPIX_APP_KEY)")
            return False
        try:
            import requests  # noqa: F401
            return True
        except ImportError:
            return False

    def version_info(self) -> str:
        if self.is_available():
            return "Mathpix Convert API"
        return "Mathpix (not configured — set MATHPIX_APP_ID and MATHPIX_APP_KEY)"

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        start = time.time()
        logger.info(
            "mathpix: converting %s → %s (%s)",
            source_format, target_format, input_path.name,
        )

        if target_format != "latex":
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=time.time() - start,
                source_format=source_format, target_format=target_format,
                error_message=f"Mathpix only targets LaTeX, not {target_format}",
            )

        if source_format not in ("pdf", "png", "jpg"):
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=time.time() - start,
                source_format=source_format, target_format=target_format,
                error_message=f"Mathpix only accepts PDF/image sources, not {source_format}",
            )

        try:
            import requests

            app_id = os.environ["MATHPIX_APP_ID"]
            app_key = os.environ["MATHPIX_APP_KEY"]

            # Step 1: Upload the file
            headers = {
                "app_id": app_id,
                "app_key": app_key,
            }

            with open(input_path, "rb") as f:
                files = {"file": (input_path.name, f)}
                options = {
                    "conversion_formats": {"tex.zip": True},
                    "math_inline_delimiters": ["$", "$"],
                    "math_display_delimiters": ["$$", "$$"],
                }

                import json
                response = requests.post(
                    "https://api.mathpix.com/v3/pdf",
                    headers=headers,
                    files=files,
                    data={"options_json": json.dumps(options)},
                    timeout=60,
                )

            if response.status_code != 200:
                return ConversionResult(
                    success=False, output_path=None, backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format, target_format=target_format,
                    error_message=f"Mathpix API error {response.status_code}: {response.text[:200]}",
                )

            pdf_id = response.json().get("pdf_id")
            if not pdf_id:
                return ConversionResult(
                    success=False, output_path=None, backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format, target_format=target_format,
                    error_message="Mathpix API did not return a pdf_id",
                )

            # Step 2: Poll for completion
            logger.debug("mathpix: waiting for processing (pdf_id=%s)", pdf_id)
            import time as time_mod
            for attempt in range(60):
                time_mod.sleep(2)
                status_resp = requests.get(
                    f"https://api.mathpix.com/v3/pdf/{pdf_id}",
                    headers=headers,
                    timeout=30,
                )
                status = status_resp.json().get("status", "")
                pct = status_resp.json().get("percent_done", 0)
                logger.debug("mathpix: status=%s, percent=%s%%", status, pct)

                if status == "completed":
                    break
                elif status == "error":
                    return ConversionResult(
                        success=False, output_path=None, backend_name=self.name,
                        duration_seconds=time.time() - start,
                        source_format=source_format, target_format=target_format,
                        error_message="Mathpix processing error",
                    )
            else:
                return ConversionResult(
                    success=False, output_path=None, backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format, target_format=target_format,
                    error_message="Mathpix processing timed out (120s)",
                )

            # Step 3: Download LaTeX result
            tex_resp = requests.get(
                f"https://api.mathpix.com/v3/pdf/{pdf_id}.tex",
                headers=headers,
                timeout=30,
            )
            if tex_resp.status_code != 200:
                return ConversionResult(
                    success=False, output_path=None, backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format, target_format=target_format,
                    error_message=f"Failed to download LaTeX: {tex_resp.status_code}",
                )

            output_path.write_text(tex_resp.text, encoding="utf-8")
            duration = time.time() - start
            size = output_path.stat().st_size

            logger.info(
                "mathpix: conversion complete in %.2fs (%d bytes)",
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

        except ImportError as e:
            duration = time.time() - start
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=f"requests not installed: {e}",
            )

        except Exception as e:
            duration = time.time() - start
            logger.error("mathpix: conversion failed: %s", e, exc_info=True)
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=str(e),
            )
