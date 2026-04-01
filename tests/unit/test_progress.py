"""Tests for the progress display module."""

import time

from rich.console import Console

from doc_shape_shifter.utils.progress import ConversionProgress


class TestConversionProgress:
    """Test progress bar context manager."""

    def test_context_manager_completes(self):
        """Progress bar should start and stop without error."""
        console = Console(stderr=True, quiet=True)
        with ConversionProgress(
            "md -> txt", "builtin", eta_seconds=0.5, console=console
        ):
            time.sleep(0.1)
        # No exception means success

    def test_short_conversion(self):
        """Very short conversion should complete cleanly."""
        console = Console(stderr=True, quiet=True)
        with ConversionProgress(
            "json -> csv", "builtin", eta_seconds=0.1, console=console
        ):
            pass  # instant

    def test_progress_with_zero_eta(self):
        """Zero ETA should not crash."""
        console = Console(stderr=True, quiet=True)
        with ConversionProgress(
            "test -> test", "test", eta_seconds=0.0, console=console
        ):
            time.sleep(0.1)

    def test_progress_with_large_eta(self):
        """Large ETA should work (we exit early)."""
        console = Console(stderr=True, quiet=True)
        with ConversionProgress(
            "pdf -> md", "docling", eta_seconds=60.0, console=console
        ):
            time.sleep(0.1)

    def test_attributes(self):
        """Progress object should expose description and backend."""
        p = ConversionProgress("a -> b", "pandoc", eta_seconds=1.0)
        assert p.description == "a -> b"
        assert p.backend_name == "pandoc"
        assert p.eta_seconds == 1.0
