"""Backend registry — discovers and exposes all available conversion backends."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseBackend

logger = logging.getLogger("doc_shape_shifter.backends")

_BACKEND_CLASSES: dict[str, type["BaseBackend"]] = {}
_BACKEND_INSTANCES: dict[str, "BaseBackend"] = {}


def _register_backends() -> None:
    """Import and register all backend classes."""
    from .builtin_backend import BuiltinBackend
    from .docling_backend import DoclingBackend
    from .markitdown_backend import MarkItDownBackend
    from .mathpix_backend import MathpixBackend
    from .pandoc_backend import PandocBackend
    from .pymupdf_backend import PyMuPDFBackend
    from .tabula_backend import TabulaBackend

    for cls in [
        BuiltinBackend, PyMuPDFBackend, PandocBackend, DoclingBackend,
        MarkItDownBackend, TabulaBackend, MathpixBackend,
    ]:
        _BACKEND_CLASSES[cls.name] = cls


def get_backend(name: str) -> "BaseBackend":
    """Get a backend instance by name (singleton per name)."""
    if not _BACKEND_CLASSES:
        _register_backends()

    if name not in _BACKEND_CLASSES:
        raise KeyError(
            f"Unknown backend: '{name}'. Available: {', '.join(_BACKEND_CLASSES)}"
        )

    if name not in _BACKEND_INSTANCES:
        _BACKEND_INSTANCES[name] = _BACKEND_CLASSES[name]()
        logger.debug("Instantiated backend: %s", name)

    return _BACKEND_INSTANCES[name]


def list_backends() -> list[tuple[str, bool]]:
    """List all known backends with their availability status."""
    if not _BACKEND_CLASSES:
        _register_backends()

    results = []
    for name in sorted(_BACKEND_CLASSES):
        try:
            backend = get_backend(name)
            results.append((name, backend.is_available()))
        except Exception:
            results.append((name, False))
    return results
