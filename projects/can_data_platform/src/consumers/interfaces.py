"""Consumer interfaces and result models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BatchConsumerResult:
    """Result of consuming a batch of messages."""

    consumed: int
    messages_processed: int  # Changed from 'processed' to match app expectations
    messages_deleted: int  # Changed from 'deleted' to match app expectations
    errors: int  # Changed from 'failed' to match app expectations
    deletion_errors: int  # Added to match app expectations
    processing_time: float

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.messages_processed == 0:
            return 0.0
        return (self.messages_deleted / self.messages_processed) * 100

    @classmethod
    def create_empty(cls) -> "BatchConsumerResult":
        """Create an empty result for no messages."""
        return cls(
            consumed=0,
            messages_processed=0,
            messages_deleted=0,
            errors=0,
            deletion_errors=0,
            processing_time=0.0,
        )


class ConsumerInterface(ABC):
    """Interface for message consumers following Interface Segregation Principle."""

    @abstractmethod
    def consume_batch(self) -> BatchConsumerResult:
        """Consume and process a batch of messages.

        Returns:
            BatchConsumerResult with processing statistics
        """
        raise NotImplementedError

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the consumer is in a healthy state.

        Returns:
            True if consumer is healthy, False otherwise
        """
        raise NotImplementedError

    def health_check(self) -> bool:
        """Alias for is_healthy for backward compatibility."""
        return self.is_healthy()

    @abstractmethod
    def close(self) -> None:
        """Clean up consumer resources."""
        raise NotImplementedError
