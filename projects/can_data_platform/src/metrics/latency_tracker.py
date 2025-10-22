"""Latency tracking implementation with configurable output and alerts."""

import json
import logging
import statistics
from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast

from .interfaces import LatencyTrackerInterface


logger = logging.getLogger(__name__)


class LatencyTracker(LatencyTrackerInterface):
    """Tracks SQS, batch processing, and end-to-end latencies following SRP.

    Collects latency metrics and periodically flushes percentiles to JSONL files.
    Provides alerting for SLA violations.
    """

    def __init__(
        self,
        flush_every: int = 100,
        output_dir: Optional[str] = None,
        sla_threshold_seconds: float = 5.0,
    ):
        """Initialize latency tracker.

        Args:
            flush_every: Events between flushes
            output_dir: Directory for output files
            sla_threshold_seconds: SLA threshold for alerts
        """
        self.flush_every = flush_every
        self.sla_threshold_seconds = sla_threshold_seconds

        # Event counters
        self.events_seen = 0
        self.total_events_processed = 0
        self.events_in_current_batch = 0

        # Metric collections
        self.sqs_latencies: List[float] = []
        self.batch_write_latencies: List[float] = []
        self.e2e_latencies: List[float] = []
        self.queue_age_latencies: List[float] = []  # New: track queue age

        # Setup output directory
        if output_dir is None:
            self.output_dir = Path("projects/can_data_platform/data/metrics")
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "LatencyTracker initialized: flush_every=%d, sla_threshold=%.1fs",
            flush_every,
            sla_threshold_seconds,
        )

    def record_sqs_latency(self, start_time: float, end_time: float) -> None:
        """Record SQS polling latency in milliseconds."""
        latency_ms = (end_time - start_time) * 1000
        self.sqs_latencies.append(latency_ms)
        logger.debug("SQS latency recorded: %.2fms", latency_ms)

    def record_batch_write_latency(self, start_time: float, end_time: float) -> None:
        """Record batch processing latency in milliseconds."""
        latency_ms = (end_time - start_time) * 1000
        self.batch_write_latencies.append(latency_ms)
        logger.debug("Batch write latency recorded: %.2fms", latency_ms)

    def record_e2e_latency(
        self, event_timestamp: float, process_timestamp: float
    ) -> None:
        """Record end-to-end latency from event generation to processing."""
        e2e_seconds = process_timestamp - event_timestamp
        self.e2e_latencies.append(e2e_seconds)
        logger.debug("E2E latency recorded: %.2fs", e2e_seconds)

    def record_queue_age_latency(
        self, message_sent_timestamp: str, receive_timestamp: float
    ) -> None:
        """Track how long messages sit in SQS queue.

        Args:
            message_sent_timestamp: SQS SentTimestamp (milliseconds since epoch)
            receive_timestamp: When message was received (seconds since epoch)
        """
        try:
            # Parse SQS SentTimestamp (milliseconds since epoch)
            sent_ts = float(message_sent_timestamp) / 1000.0
            queue_latency = receive_timestamp - sent_ts
            self.queue_age_latencies.append(queue_latency)
            logger.debug("Queue age latency recorded: %.2fs", queue_latency)
        except (ValueError, TypeError) as e:
            logger.warning("Failed to calculate queue latency: %s", e)

    def step_event(self) -> None:
        """Step the event counter and flush metrics if needed."""
        # Increment counters only. Flushing must happen atomically after a
        # full SQS batch is processed to avoid clearing metrics mid-batch.
        self.events_seen += 1
        self.total_events_processed += 1
        self.events_in_current_batch += 1

    def should_flush(self) -> bool:
        """Return True when accumulated events reach the configured flush threshold.

        This separates the act of counting events from performing the flush so
        callers (for example the SQS consumer) can flush once a batch has been
        fully processed and deletions have been attempted.
        """
        return self.events_in_current_batch >= self.flush_every

    def flush_metrics(self) -> None:
        """Flush accumulated metrics to JSONL file and clear collections."""
        batch_number = self.events_seen // self.flush_every

        metrics = {
            "batch": batch_number,
            "timestamp": datetime.now().isoformat(),
            "events_in_batch": self.events_in_current_batch,
            "total_events_processed": self.total_events_processed,
            # SQS polling metrics
            "sqs_poll_p50_ms": self._calculate_percentile(self.sqs_latencies, 50),
            "sqs_poll_p95_ms": self._calculate_percentile(self.sqs_latencies, 95),
            "sqs_poll_p99_ms": self._calculate_percentile(self.sqs_latencies, 99),
            "sqs_poll_count": len(self.sqs_latencies),
            # Batch processing metrics
            "batch_write_p50_ms": self._calculate_percentile(
                self.batch_write_latencies, 50
            ),
            "batch_write_p95_ms": self._calculate_percentile(
                self.batch_write_latencies, 95
            ),
            "batch_write_p99_ms": self._calculate_percentile(
                self.batch_write_latencies, 99
            ),
            "batch_write_count": len(self.batch_write_latencies),
            # End-to-end metrics
            "e2e_p50_s": self._calculate_percentile(self.e2e_latencies, 50),
            "e2e_p95_s": self._calculate_percentile(self.e2e_latencies, 95),
            "e2e_p99_s": self._calculate_percentile(self.e2e_latencies, 99),
            "e2e_count": len(self.e2e_latencies),
            # Queue age metrics
            "queue_age_p50_s": self._calculate_percentile(self.queue_age_latencies, 50),
            "queue_age_p95_s": self._calculate_percentile(self.queue_age_latencies, 95),
            "queue_age_p99_s": self._calculate_percentile(self.queue_age_latencies, 99),
            "queue_age_count": len(self.queue_age_latencies),
        }

        # Always clear internal state after generating metrics
        should_write_metrics = (
            cast(int, metrics["e2e_count"]) > 0
            or cast(int, metrics["batch_write_count"]) > 0
            or cast(int, metrics["sqs_poll_count"]) > 0
        )

        if should_write_metrics:
            # Write metrics to file
            self._write_metrics_to_file(metrics)

            # Log metrics
            logger.info("Latency metrics flushed: %s", metrics)
            print(f"📊 [LATENCY METRICS] Batch {batch_number}: {metrics}")

            # Check SLA violations
            self._check_sla_violations(metrics)
        else:
            logger.debug("Skipped flushing empty latency batch %d", batch_number)

        # Always clear collections for next batch (critical for preventing accumulation)
        self._clear_metrics()

    def _calculate_percentile(
        self, values: List[float], percentile: int
    ) -> Optional[float]:
        """Calculate percentile for a list of values.

        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            Calculated percentile or None if no values
        """
        if not values:
            return None

        try:
            if len(values) == 1:
                return round(values[0], 2)

            # Use statistics.quantiles for proper percentile calculation
            quantiles = statistics.quantiles(values, n=100)
            return round(quantiles[percentile - 1], 2)

        except (ValueError, IndexError):
            # Fallback to median for edge cases
            return round(statistics.median(values), 2)

    def _write_metrics_to_file(self, metrics: dict) -> None:
        """Write metrics to JSONL file."""
        try:
            output_file = self.output_dir / f"latency-{datetime.now().date()}.jsonl"

            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics, separators=(',', ':')) + "\n")

            logger.debug("Metrics written to %s", output_file)

        except (OSError, IOError) as e:
            logger.error("Failed to write metrics to file: %s", e)

    def _check_sla_violations(self, metrics: dict) -> None:
        """Check for SLA violations and log alerts."""
        e2e_p95 = metrics.get("e2e_p95_s")

        if e2e_p95 is not None and e2e_p95 > self.sla_threshold_seconds:
            alert_msg = (
                f"🚨 [SLA VIOLATION] P95 E2E latency ({e2e_p95:.2f}s) "
                f"exceeds SLA threshold ({self.sla_threshold_seconds:.1f}s)!"
            )
            logger.warning(alert_msg)
            print(alert_msg)

    def _clear_metrics(self) -> None:
        """Clear metric collections for the next batch."""
        logger.debug(
            "Clearing metrics: %d SQS, %d batch_write, %d e2e, %d queue_age latencies",
            len(self.sqs_latencies),
            len(self.batch_write_latencies),
            len(self.e2e_latencies),
            len(self.queue_age_latencies),
        )
        self.sqs_latencies.clear()
        self.batch_write_latencies.clear()
        self.e2e_latencies.clear()
        self.queue_age_latencies.clear()
        self.events_in_current_batch = 0  # Reset batch counter
        logger.debug("Metrics cleared successfully")

    def get_current_stats(self) -> dict:
        """Get current statistics without flushing.

        Returns:
            Dictionary with current metric counts and basic stats
        """
        return {
            "events_seen": self.events_seen,
            "total_events_processed": self.total_events_processed,
            "sqs_latencies_count": len(self.sqs_latencies),
            "batch_write_latencies_count": len(self.batch_write_latencies),
            "e2e_latencies_count": len(self.e2e_latencies),
            "next_flush_at": (
                ((self.events_seen // self.flush_every) + 1) * self.flush_every
            ),
        }

    def flush(self) -> None:
        """Force flush any pending metrics to file."""
        if (
            len(self.sqs_latencies) > 0
            or len(self.batch_write_latencies) > 0
            or len(self.e2e_latencies) > 0
        ):
            self.flush_metrics()


class NoOpLatencyTracker(LatencyTrackerInterface):
    """No-operation latency tracker for when metrics are disabled."""

    def record_sqs_latency(self, start_time: float, end_time: float) -> None:
        """No-op SQS latency recording."""

    def record_batch_write_latency(self, start_time: float, end_time: float) -> None:
        """No-op batch write latency recording."""

    def record_e2e_latency(
        self, event_timestamp: float, process_timestamp: float
    ) -> None:
        """No-op E2E latency recording."""

    def record_queue_age_latency(
        self, message_sent_timestamp: str, receive_timestamp: float
    ) -> None:
        """No-op queue age latency recording."""

    def should_flush(self) -> bool:
        """No-op should flush check."""
        return False

    def step_event(self) -> None:
        """No-op event stepping."""

    def flush(self) -> None:
        """No-op flush operation."""

    def flush_metrics(self) -> None:
        """No-op metrics flushing."""


class LatencyTrackerFactory:
    """Factory for creating latency trackers."""

    @staticmethod
    def create_standard_tracker(
        flush_every: int = 100,
        output_dir: Optional[str] = None,
        sla_threshold_seconds: float = 5.0,
    ) -> LatencyTracker:
        """Create a standard latency tracker.

        Args:
            flush_every: Events between flushes
            output_dir: Output directory for metrics
            sla_threshold_seconds: SLA threshold for alerts

        Returns:
            Configured LatencyTracker instance
        """
        return LatencyTracker(
            flush_every=flush_every,
            output_dir=output_dir,
            sla_threshold_seconds=sla_threshold_seconds,
        )

    @staticmethod
    def create_noop_tracker() -> NoOpLatencyTracker:
        """Create a no-operation latency tracker."""
        return NoOpLatencyTracker()
