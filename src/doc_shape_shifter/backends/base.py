"""Abstract base class for all conversion backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConversionResult:
    """Result of a conversion operation with metadata for logging/debugging."""

    success: bool
    output_path: Path | None
    backend_name: str
    duration_seconds: float
    source_format: str
    target_format: str
    error_message: str | None = None
    file_size_bytes: int | None = None
    estimated_seconds: float | None = None
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "OK" if self.success else "FAILED"
        return (
            f"[{status}] {self.source_format} -> {self.target_format} "
            f"via {self.backend_name} ({self.duration_seconds:.2f}s)"
        )


class BaseBackend(ABC):
    """Abstract base class that all conversion backends must implement."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend's dependencies are installed and functional."""

    @abstractmethod
    def convert(
        self,
        input_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        """Execute a format conversion."""

    def version_info(self) -> str:
        """Return version string for this backend (for diagnostics)."""
        return "unknown"
