"""Tabula backend — PDF table extraction to CSV/JSON."""

import logging
import time
from pathlib import Path

from .base import BaseBackend, ConversionResult

logger = logging.getLogger("doc_shape_shifter.backends.tabula")


class TabulaBackend(BaseBackend):
    """Backend using tabula-py for extracting tables from PDFs."""

    name = "tabula"

    def is_available(self) -> bool:
        try:
            import shutil

            import tabula  # noqa: F401
            return shutil.which("java") is not None
        except ImportError:
            return False

    def version_info(self) -> str:
        try:
            import tabula
            return f"tabula-py {getattr(tabula, '__version__', 'unknown')}"
        except ImportError:
            return "tabula-py (not installed)"

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        start = time.time()
        logger.info(
            "tabula: extracting tables %s -> %s (%s)",
            source_format, target_format, input_path.name,
        )

        if source_format != "pdf" or target_format not in ("csv", "json"):
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=time.time() - start,
                source_format=source_format, target_format=target_format,
                error_message=(
                    f"Tabula only supports PDF -> CSV/JSON, "
                    f"not {source_format} -> {target_format}"
                ),
            )

        try:
            import tabula

            dfs = tabula.read_pdf(str(input_path), pages="all", multiple_tables=True)

            if not dfs:
                return ConversionResult(
                    success=False, output_path=None, backend_name=self.name,
                    duration_seconds=time.time() - start,
                    source_format=source_format, target_format=target_format,
                    error_message="No tables found in PDF",
                )

            logger.debug("tabula: found %d tables", len(dfs))

            if target_format == "csv":
                parts = []
                for i, df in enumerate(dfs):
                    if i > 0:
                        parts.append(f"\n# --- Table {i + 1} ---\n")
                    parts.append(df.to_csv(index=False))
                output_path.write_text("".join(parts), encoding="utf-8")

            elif target_format == "json":
                import json
                all_tables = []
                for i, df in enumerate(dfs):
                    all_tables.append({
                        "table_index": i,
                        "rows": df.shape[0],
                        "columns": list(df.columns),
                        "data": df.to_dict(orient="records"),
                    })
                output_path.write_text(
                    json.dumps(all_tables, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8",
                )

            duration = time.time() - start
            size = output_path.stat().st_size

            logger.info(
                "tabula: extracted %d tables in %.2fs",
                len(dfs), duration,
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
                error_message=f"tabula-py not installed: {e}. Install: pip install tabula-py",
            )

        except Exception as e:
            duration = time.time() - start
            logger.error("tabula: extraction failed: %s", e, exc_info=True)
            return ConversionResult(
                success=False, output_path=None, backend_name=self.name,
                duration_seconds=duration,
                source_format=source_format, target_format=target_format,
                error_message=str(e),
            )
