from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def command_version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None

    if completed.returncode != 0:
        return None
    for line in completed.stdout.splitlines():
        text = line.strip()
        if text:
            return text
    return None


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        joined = " ".join(command)
        raise RuntimeError(f"Command failed: {joined}\n{stderr}")
    return completed


def preferred_pdf_engine() -> str | None:
    for engine in ("tectonic", "pdflatex", "wkhtmltopdf"):
        if command_exists(engine):
            return engine
    return None


def mathpix_credentials_present() -> bool:
    return bool(os.environ.get("MATHPIX_APP_ID") and os.environ.get("MATHPIX_APP_KEY"))
