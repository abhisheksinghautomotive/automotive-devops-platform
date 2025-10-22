"""Factory for creating latency tracker instances."""

from typing import Optional
from ..metrics.interfaces import LatencyTrackerInterface
from ..metrics.latency_tracker import LatencyTracker, NoOpLatencyTracker


class LatencyTrackerFactory:
    """Factory for creating latency tracker instances."""

    @staticmethod
    def create_tracker(
        enabled: bool = True,
        output_dir: Optional[str] = None,
        flush_every: int = 100,
        sla_threshold_seconds: float = 5.0,
    ) -> LatencyTrackerInterface:
        """Create a latency tracker instance.

        Args:
            enabled: Whether to enable latency tracking
            output_dir: Directory for latency metrics output
            flush_every: Number of measurements before flushing
            sla_threshold_seconds: SLA threshold in seconds

        Returns:
            LatencyTrackerInterface instance
        """
        if not enabled or output_dir is None:
            return NoOpLatencyTracker()

        return LatencyTracker(
            output_dir=output_dir,
            flush_every=flush_every,
            sla_threshold_seconds=sla_threshold_seconds,
        )
