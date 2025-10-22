"""Progress tracking implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from tqdm import tqdm  # type: ignore


class ProgressTracker(ABC):
    """Abstract progress tracker following Interface Segregation Principle."""

    @abstractmethod
    def start(self, total: int, description: str) -> None:
        """Start progress tracking."""
        raise NotImplementedError

    @abstractmethod
    def update(self, n: int = 1) -> None:
        """Update progress by n units."""
        raise NotImplementedError

    @abstractmethod
    def set_postfix(self, postfix: Dict[str, Any]) -> None:
        """Set postfix information."""
        raise NotImplementedError

    @abstractmethod
    def write(self, message: str) -> None:
        """Write a message without disrupting progress."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the progress tracker."""
        raise NotImplementedError


class TqdmProgressTracker(ProgressTracker):
    """tqdm-based progress tracker implementation."""

    def __init__(self, unit: str = "items"):
        """Initialize progress tracker.

        Args:
            unit: Unit of measurement for progress
        """
        self.unit = unit
        self._progress_bar: Optional[tqdm] = None

    def start(self, total: int, description: str) -> None:
        """Start progress tracking with tqdm."""
        self._progress_bar = tqdm(
            total=total,
            desc=description,
            unit=self.unit,
            bar_format=(
                "{l_bar}{bar}| {n_fmt}/{total_fmt} "
                "[{elapsed}<{remaining}, {rate_fmt}]"
            ),
        )

    def update(self, n: int = 1) -> None:
        """Update progress by n units."""
        if self._progress_bar:
            self._progress_bar.update(n)

    def set_postfix(self, postfix: Dict[str, Any]) -> None:
        """Set postfix information."""
        if self._progress_bar:
            self._progress_bar.set_postfix(postfix)

    def write(self, message: str) -> None:
        """Write a message without disrupting progress."""
        if self._progress_bar:
            self._progress_bar.write(message)

    def close(self) -> None:
        """Close the progress tracker."""
        if self._progress_bar:
            self._progress_bar.close()
            self._progress_bar = None


class NoOpProgressTracker(ProgressTracker):
    """No-operation progress tracker for when progress tracking is disabled."""

    def start(self, total: int, description: str) -> None:
        """No-op start."""

    def update(self, n: int = 1) -> None:
        """No-op update."""

    def set_postfix(self, postfix: Dict[str, Any]) -> None:
        """No-op set postfix."""

    def write(self, message: str) -> None:
        """No-op write."""

    def close(self) -> None:
        """No-op close."""


class ProgressTrackerFactory:
    """Factory for creating progress trackers."""

    @staticmethod
    def create_tqdm_tracker(unit: str = "items") -> TqdmProgressTracker:
        """Create a tqdm progress tracker."""
        return TqdmProgressTracker(unit)

    @staticmethod
    def create_noop_tracker() -> NoOpProgressTracker:
        """Create a no-operation progress tracker."""
        return NoOpProgressTracker()
