"""Publisher interfaces and result models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..tracking import ProgressTracker


@dataclass
class PublishResult:
    """Result of a publishing operation."""

    successes: int
    failures: int
    batches: int
    retries: int

    @property
    def total_processed(self) -> int:
        """Total number of events processed."""
        return self.successes + self.failures

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.successes / self.total_processed) * 100


class PublisherInterface(ABC):
    """Interface for event publishers following Interface Segregation Principle."""

    @abstractmethod
    def publish(
        self,
        events: List[Dict[str, Any]],
        progress_tracker: Optional["ProgressTracker"] = None,
    ) -> PublishResult:
        """Publish a list of events.

        Args:
            events: List of event dictionaries to publish
            progress_tracker: Optional progress tracker for real-time updates

        Returns:
            PublishResult with operation statistics
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        raise NotImplementedError
