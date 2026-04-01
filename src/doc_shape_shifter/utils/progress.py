"""Progress display for conversions using Rich."""

from __future__ import annotations

import threading
import time

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)


class ConversionProgress:
    """Manages a Rich progress bar for a conversion operation.

    Usage:
        with ConversionProgress("pdf -> md", "pandoc", eta_seconds=2.5) as p:
            # ... backend does its work ...
            # progress auto-advances based on elapsed time vs ETA
        # bar completes when context exits

    The progress bar updates automatically in a background thread,
    advancing proportionally to elapsed_time / estimated_total_time.
    This works well because most backends are opaque (no internal
    progress callbacks), so time-based estimation is the best we can do.
    """

    def __init__(
        self,
        description: str,
        backend_name: str,
        eta_seconds: float = 1.0,
        console: Console | None = None,
    ) -> None:
        self.description = description
        self.backend_name = backend_name
        self.eta_seconds = max(eta_seconds, 0.1)
        self._console = console or Console(stderr=True)
        self._progress: Progress | None = None
        self._task_id = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._start_time: float = 0.0

    def __enter__(self) -> ConversionProgress:
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("{task.percentage:>3.0f}%"),
            TextColumn("ETA {task.fields[eta]}"),
            TimeElapsedColumn(),
            console=self._console,
            transient=True,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            f"{self.description} via {self.backend_name}",
            total=100,
            eta=_format_eta(self.eta_seconds),
        )
        self._start_time = time.monotonic()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._updater, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._progress is not None and self._task_id is not None:
            # Jump to 100% on completion
            self._progress.update(
                self._task_id,
                completed=100,
                eta="done",
            )
            self._progress.stop()
        return None

    def _updater(self) -> None:
        """Background thread that advances the bar based on elapsed time."""
        while not self._stop_event.is_set():
            elapsed = time.monotonic() - self._start_time
            # Use asymptotic curve: progress approaches 95% as time -> eta,
            # never quite reaching 100% until __exit__ forces it.
            # This avoids the bar sitting at 100% while still processing.
            if self.eta_seconds > 0:
                fraction = elapsed / self.eta_seconds
                # Asymptotic: 95 * (1 - e^(-2*fraction))
                # At fraction=1.0 (elapsed==eta), shows ~82%
                # At fraction=2.0, shows ~93%
                import math
                pct = 95.0 * (1.0 - math.exp(-2.0 * fraction))
            else:
                pct = 90.0

            remaining = max(0.0, self.eta_seconds - elapsed)
            if self._progress is not None and self._task_id is not None:
                self._progress.update(
                    self._task_id,
                    completed=min(pct, 95.0),
                    eta=_format_eta(remaining),
                )
            self._stop_event.wait(timeout=0.25)


def _format_eta(seconds: float) -> str:
    """Format seconds into a short ETA string for the progress bar."""
    if seconds <= 0:
        return "done"
    if seconds < 1.0:
        return "<1s"
    if seconds < 60.0:
        return f"{seconds:.0f}s"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    if secs == 0:
        return f"{minutes}m"
    return f"{minutes}m {secs}s"
