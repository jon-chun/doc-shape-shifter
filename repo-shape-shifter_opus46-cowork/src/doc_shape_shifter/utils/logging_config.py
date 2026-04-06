"""Structured JSON logging configuration for doc-shape-shifter."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects (JSONL format)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach any extra fields passed via `extra={}` kwarg
        for key in ("source_format", "target_format", "backend", "duration_s",
                     "input_file", "output_file", "file_size_bytes", "error"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry)


def setup_logging(verbosity: int = 0) -> logging.Logger:
    """Configure logging with both console (Rich-style) and file (JSON) handlers.

    Args:
        verbosity: 0=WARNING, 1=INFO, 2+=DEBUG

    Returns:
        Root logger for the package.
    """
    level_map = {0: logging.WARNING, 1: logging.INFO}
    level = level_map.get(verbosity, logging.DEBUG)

    logger = logging.getLogger("doc_shape_shifter")
    logger.setLevel(logging.DEBUG)  # Capture all; handlers filter

    # Clear any existing handlers (prevents duplicate logs on re-init)
    logger.handlers.clear()

    # Console handler — human-readable
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console_fmt = logging.Formatter(
        "[%(levelname)-7s] %(message)s"
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    # File handler — structured JSON lines
    today = datetime.now().strftime("%Y%m%d")
    log_file = LOG_DIR / f"dss_{today}.jsonl"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    logger.debug(
        "Logging initialized: console=%s, file=%s",
        logging.getLevelName(level),
        log_file,
    )
    return logger
