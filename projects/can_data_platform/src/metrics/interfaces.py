"""Latency tracking interfaces."""

from abc import ABC, abstractmethod


class LatencyTrackerInterface(ABC):
    """Interface for latency tracking following Interface Segregation Principle."""

    @abstractmethod
    def record_sqs_latency(self, start_time: float, end_time: float) -> None:
        """Record SQS polling latency.

        Args:
            start_time: Start timestamp
            end_time: End timestamp
        """
        raise NotImplementedError

    @abstractmethod
    def record_batch_write_latency(self, start_time: float, end_time: float) -> None:
        """Record batch processing latency.

        Args:
            start_time: Start timestamp
            end_time: End timestamp
        """
        raise NotImplementedError

    @abstractmethod
    def record_e2e_latency(
        self, event_timestamp: float, process_timestamp: float
    ) -> None:
        """Record end-to-end latency from event generation to processing.

        Args:
            event_timestamp: Original event timestamp
            process_timestamp: Processing timestamp
        """
        raise NotImplementedError

    @abstractmethod
    def record_queue_age_latency(
        self, message_sent_timestamp: str, receive_timestamp: float
    ) -> None:
        """Track how long messages sit in SQS queue.

        Args:
            message_sent_timestamp: SQS SentTimestamp (milliseconds since epoch)
            receive_timestamp: When message was received (seconds since epoch)
        """
        raise NotImplementedError

    @abstractmethod
    def should_flush(self) -> bool:
        """Determine if metrics should be flushed based on event count."""
        raise NotImplementedError

    @abstractmethod
    def step_event(self) -> None:
        """Step the event counter for periodic flushing."""
        raise NotImplementedError

    @abstractmethod
    def flush(self) -> None:
        """Force flush any pending metrics to file."""
        raise NotImplementedError

    @abstractmethod
    def flush_metrics(self) -> None:
        """Flush accumulated metrics to storage."""
        raise NotImplementedError
