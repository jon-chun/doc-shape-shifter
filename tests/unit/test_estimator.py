"""Tests for the time estimation module."""

import pytest

from doc_shape_shifter.utils.estimator import (
    estimate_conversion_time,
    estimate_for_file,
    format_eta,
)


class TestEstimateConversionTime:
    """Test base estimation logic."""

    def test_known_builtin_pair(self):
        """Builtin md->txt should be very fast."""
        t = estimate_conversion_time("builtin", "md", "txt")
        assert 0 < t < 1.0

    def test_known_pandoc_pair(self):
        """Pandoc md->pdf should be ~2s base."""
        t = estimate_conversion_time("pandoc", "md", "pdf")
        assert t >= 1.0

    def test_known_docling_pair(self):
        """Docling pdf->md should be ~5s base."""
        t = estimate_conversion_time("docling", "pdf", "md")
        assert t >= 3.0

    def test_known_mathpix_pair(self):
        """Mathpix should estimate very high due to network."""
        t = estimate_conversion_time("mathpix", "pdf", "latex")
        assert t >= 20.0

    def test_known_tabula_pair(self):
        """Tabula pdf->csv has Java overhead."""
        t = estimate_conversion_time("tabula", "pdf", "csv")
        assert t >= 2.0

    def test_unknown_pair_uses_backend_default(self):
        """Unknown format pair should fall back to backend default."""
        t = estimate_conversion_time("pandoc", "xyz", "abc")
        assert t == pytest.approx(0.5, abs=0.01)

    def test_unknown_backend_returns_1s(self):
        """Completely unknown backend defaults to 1.0s."""
        t = estimate_conversion_time("nonexistent", "a", "b")
        assert t == pytest.approx(1.0, abs=0.01)

    def test_small_file_returns_base(self):
        """Files <= 10 KB should return the base estimate."""
        base = estimate_conversion_time("builtin", "md", "txt")
        with_size = estimate_conversion_time("builtin", "md", "txt", file_size_bytes=5000)
        assert with_size == base

    def test_none_size_returns_base(self):
        """None file size should return the base estimate."""
        base = estimate_conversion_time("builtin", "md", "txt")
        with_none = estimate_conversion_time("builtin", "md", "txt", file_size_bytes=None)
        assert with_none == base

    def test_large_file_scales_up(self):
        """A 10 MB file should estimate more time than base."""
        base = estimate_conversion_time("pandoc", "md", "docx")
        large = estimate_conversion_time("pandoc", "md", "docx", file_size_bytes=10 * 1024 * 1024)
        assert large > base

    def test_scaling_is_proportional(self):
        """Doubling file size should roughly double the extra time."""
        size_5mb = estimate_conversion_time("pandoc", "md", "html", file_size_bytes=5 * 1024 * 1024)
        size_10mb = estimate_conversion_time(
            "pandoc", "md", "html", file_size_bytes=10 * 1024 * 1024
        )
        base = estimate_conversion_time("pandoc", "md", "html")
        extra_5 = size_5mb - base
        extra_10 = size_10mb - base
        assert extra_10 == pytest.approx(extra_5 * 2, rel=0.1)

    def test_docling_scales_more_than_builtin(self):
        """Docling should scale more aggressively than builtin for large files."""
        size = 5 * 1024 * 1024
        docling_t = estimate_conversion_time("docling", "pdf", "md", file_size_bytes=size)
        builtin_t = estimate_conversion_time("builtin", "md", "txt", file_size_bytes=size)
        assert docling_t > builtin_t


class TestEstimateForFile:
    """Test file-based estimation."""

    def test_existing_file(self, tmp_path):
        """Should use actual file size."""
        f = tmp_path / "test.md"
        f.write_text("x" * 50000)
        t = estimate_for_file("pandoc", "md", "html", f)
        base = estimate_conversion_time("pandoc", "md", "html")
        assert t >= base

    def test_nonexistent_file(self, tmp_path):
        """Should fall back to base estimate."""
        t = estimate_for_file("pandoc", "md", "html", tmp_path / "missing.md")
        base = estimate_conversion_time("pandoc", "md", "html")
        assert t == base

    def test_empty_file(self, tmp_path):
        """Empty file should return base estimate."""
        f = tmp_path / "empty.md"
        f.write_text("")
        t = estimate_for_file("pandoc", "md", "html", f)
        base = estimate_conversion_time("pandoc", "md", "html")
        assert t == base


class TestFormatEta:
    """Test human-readable ETA formatting."""

    def test_sub_second(self):
        assert format_eta(0.3) == "<1s"
        assert format_eta(0.0) == "<1s"

    def test_seconds(self):
        assert format_eta(5.0) == "~5s"
        assert format_eta(30.0) == "~30s"
        assert format_eta(59.9) == "~60s"

    def test_minutes(self):
        assert format_eta(60.0) == "~1m"
        assert format_eta(65.0) == "~1m 5s"
        assert format_eta(125.0) == "~2m 5s"
        assert format_eta(120.0) == "~2m"

    def test_one_second(self):
        assert format_eta(1.0) == "~1s"
