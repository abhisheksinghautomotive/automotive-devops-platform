"""Message processor interfaces and result models."""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, Dict


logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single message."""

    success: bool
    event_timestamp: Optional[float] = None
    error_message: Optional[str] = None
    processed_data: Optional[Dict[str, Any]] = None

    @classmethod
    def success_result(
        cls,
        event_timestamp: Optional[float] = None,
        processed_data: Optional[Dict[str, Any]] = None,
    ) -> "ProcessingResult":
        """Create a successful processing result."""
        return cls(
            success=True, event_timestamp=event_timestamp, processed_data=processed_data
        )

    @classmethod
    def failure_result(cls, error_message: str) -> "ProcessingResult":
        """Create a failed processing result."""
        return cls(success=False, error_message=error_message)


class MessageProcessor(ABC):
    """Abstract interface for message processors.

    Follows Interface Segregation Principle.
    """

    @abstractmethod
    def process_message(self, message_body: str) -> ProcessingResult:
        """Process a single SQS message body.

        Args:
            message_body: JSON string message body from SQS

        Returns:
            ProcessingResult with success status and optional data
        """
        raise NotImplementedError

    @abstractmethod
    def get_processor_name(self) -> str:
        """Get the name of this processor for logging."""
        raise NotImplementedError


class BaseMessageProcessor(MessageProcessor):
    """Base implementation with common JSON parsing functionality."""

    def __init__(self, processor_name: str = "BaseProcessor"):
        """Initialize base processor.

        Args:
            processor_name: Name for logging purposes
        """
        self.processor_name = processor_name
        self.logger = logging.getLogger(f"{__name__}.{processor_name}")

    def get_processor_name(self) -> str:
        """Get the processor name."""
        return self.processor_name

    def parse_message_json(self, message_body: str) -> Optional[Dict[str, Any]]:
        """Parse JSON message body with error handling.

        Args:
            message_body: JSON string to parse

        Returns:
            Parsed dictionary or None if parsing failed
        """
        try:
            return json.loads(message_body)
        except (ValueError, TypeError) as e:
            self.logger.error("JSON parsing failed: %s", e)
            return None

    def extract_timestamp(self, event_data: Dict[str, Any]) -> Optional[float]:
        """Extract timestamp from event data for latency tracking.

        Args:
            event_data: Parsed event dictionary

        Returns:
            Event timestamp as float or None if not found
        """
        # Try multiple common timestamp field names
        timestamp_fields = [
            "epoch_timestamp",
            "timestamp",
            "event_time",
            "created_at",
            "generated_at",
        ]

        for field in timestamp_fields:
            if field in event_data:
                try:
                    return float(event_data[field])
                except (ValueError, TypeError):
                    continue

        # Fallback to current time if no timestamp found
        self.logger.warning("No valid timestamp found in event, using current time")
        return time.time()

    def process_message(self, message_body: str) -> ProcessingResult:
        """Process a message with JSON parsing and timestamp extraction."""
        event_data = self.parse_message_json(message_body)

        if event_data is None:
            return ProcessingResult.failure_result("Failed to parse JSON message")

        # Extract timestamp for latency tracking
        event_timestamp = self.extract_timestamp(event_data)

        # Delegate to specific processing logic
        return self.process_parsed_event(event_data, event_timestamp)

    @abstractmethod
    def process_parsed_event(
        self, event_data: Dict[str, Any], event_timestamp: Optional[float]
    ) -> ProcessingResult:
        """Process a parsed event. Subclasses must implement this.

        Args:
            event_data: Parsed event dictionary
            event_timestamp: Extracted event timestamp

        Returns:
            ProcessingResult with processing outcome
        """
        raise NotImplementedError
