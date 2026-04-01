#!/usr/bin/env python3
"""Diagnostic script: check which backends are installed and functional."""

import sys
import shutil


def main():
    print("=" * 60)
    print("Doc-Shape-Shifter Backend Diagnostic")
    print("=" * 60)

    checks = [
        ("Python", lambda: f"{sys.version}"),
        ("Pandoc CLI", lambda: _cmd_version("pandoc --version")),
        ("libmagic", lambda: _try_import("magic", "python-magic")),
        ("PyMuPDF", lambda: _try_import("pymupdf", "pymupdf") or _try_import("fitz", "PyMuPDF")),
        ("pypandoc", lambda: _try_import("pypandoc", "pypandoc")),
        ("Docling", lambda: _try_import("docling", "docling")),
        ("MarkItDown", lambda: _try_import("markitdown", "markitdown[all]")),
        ("tabula-py", lambda: _try_import("tabula", "tabula-py")),
        ("Java (for tabula)", lambda: _cmd_version("java -version")),
        ("Rich", lambda: _try_import("rich", "rich")),
        ("Click", lambda: _try_import("click", "click")),
    ]

    for name, check_fn in checks:
        try:
            result = check_fn()
            if result:
                print(f"  [OK]   {name}: {result}")
            else:
                print(f"  [MISS] {name}: not found")
        except Exception as e:
            print(f"  [ERR]  {name}: {e}")

    print("=" * 60)


def _try_import(module_name: str, pip_name: str) -> str:
    try:
        mod = __import__(module_name)
        ver = getattr(mod, "__version__", "installed")
        return f"{ver}"
    except ImportError:
        return ""


def _cmd_version(cmd: str) -> str:
    import subprocess
    exe = cmd.split()[0]
    if not shutil.which(exe):
        return ""
    try:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
        first = (r.stdout or r.stderr).strip().split("\n")[0]
        return first
    except Exception:
        return ""


if __name__ == "__main__":
    main()
