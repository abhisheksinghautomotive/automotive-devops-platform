"""SQS publisher implementation with batch operations and retry logic."""

import json
import logging
import random
import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING

import boto3  # type: ignore
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore

from .interfaces import PublisherInterface, PublishResult

if TYPE_CHECKING:
    from ..tracking import ProgressTracker


logger = logging.getLogger(__name__)


class SQSPublisher(PublisherInterface):
    """SQS publisher following Single Responsibility Principle.

    Handles SQS publishing with proper error handling and retry logic.
    """

    def __init__(self, queue_url: str, region_name: str = "us-east-1"):
        """Initialize SQS publisher.

        Args:
            queue_url: SQS queue URL
            region_name: AWS region name
        """
        if not queue_url:
            raise ValueError("SQS queue URL is required")

        self.queue_url = queue_url
        self.region_name = region_name
        self.sqs_client = boto3.client("sqs", region_name=region_name)

    def publish(
        self,
        events: List[Dict[str, Any]],
        progress_tracker: Optional["ProgressTracker"] = None,
    ) -> PublishResult:
        """Publish events to SQS one by one.

        Args:
            events: List of event dictionaries
            progress_tracker: Optional progress tracker for real-time updates

        Returns:
            PublishResult with operation statistics
        """
        result = PublishResult(successes=0, failures=0, batches=0, retries=0)

        for event in events:
            if self._publish_single_event(event, result):
                result.successes += 1
            else:
                result.failures += 1

        return result

    def _publish_single_event(
        self, event: Dict[str, Any], result: PublishResult
    ) -> bool:
        """Publish a single event with retry logic."""
        max_retries = 3

        for attempt in range(max_retries + 1):
            try:
                # Add publish timestamp for latency tracking
                event["publish_timestamp"] = time.time()

                self.sqs_client.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(event, separators=(',', ':')),
                )
                return True

            except (BotoCoreError, ClientError) as e:
                result.retries += 1

                if attempt < max_retries:
                    backoff_time = (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        "Event publish failed (attempt %d/%d): %s. Retrying in %.2fs",
                        attempt + 1,
                        max_retries + 1,
                        e,
                        backoff_time,
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(
                        "Event publish permanently failed after %d attempts: %s",
                        max_retries + 1,
                        e,
                    )
                    return False

        return False

    def close(self) -> None:
        """Clean up resources."""
        # boto3 clients don't need explicit cleanup


class BatchSQSPublisher(SQSPublisher):
    """Batch SQS publisher for high-throughput operations.

    Extends SQSPublisher to add batch publishing capabilities.
    """

    def __init__(
        self,
        queue_url: str,
        region_name: str = "us-east-1",
        batch_size: int = 10,
        stream_interval: float = 0.05,
    ):
        """Initialize batch SQS publisher.

        Args:
            queue_url: SQS queue URL
            region_name: AWS region name
            batch_size: Number of messages per batch (max 10)
            stream_interval: Delay between batches in seconds
        """
        super().__init__(queue_url, region_name)
        self.batch_size = min(batch_size, 10)  # AWS SQS limitation
        self.stream_interval = stream_interval

    def publish(
        self,
        events: List[Dict[str, Any]],
        progress_tracker: Optional["ProgressTracker"] = None,
    ) -> PublishResult:
        """Publish events using batch operations.

        Args:
            events: List of event dictionaries
            progress_tracker: Optional progress tracker for real-time updates

        Returns:
            PublishResult with operation statistics
        """
        logger.info(
            "Publishing %d events to SQS (batch_size=%d, stream_interval=%.3fs)",
            len(events),
            self.batch_size,
            self.stream_interval,
        )

        result = PublishResult(successes=0, failures=0, batches=0, retries=0)

        # Create batches
        event_batches = [
            events[i : i + self.batch_size]
            for i in range(0, len(events), self.batch_size)
        ]

        for batch_idx, batch in enumerate(event_batches):
            if self._publish_batch(batch, batch_idx, result):
                result.successes += len(batch)
                result.batches += 1

                # Update progress tracker in real-time
                if progress_tracker:
                    progress_tracker.update(len(batch))
                    progress_tracker.set_postfix(
                        {
                            "✅": result.successes,
                            "❌": result.failures,
                            "📦": result.batches,
                            "🔄": result.retries,
                        }
                    )
            else:
                result.failures += len(batch)

                # Update progress tracker even on failures
                if progress_tracker:
                    progress_tracker.update(len(batch))
                    progress_tracker.set_postfix(
                        {
                            "✅": result.successes,
                            "❌": result.failures,
                            "📦": result.batches,
                            "🔄": result.retries,
                        }
                    )

            # Stream interval for throttle management
            if batch_idx < len(event_batches) - 1:
                time.sleep(self.stream_interval)

        return result

    def _publish_batch(
        self, batch: List[Dict[str, Any]], batch_idx: int, result: PublishResult
    ) -> bool:
        """Publish a single batch with retry logic."""
        entries = []

        for event_idx, event in enumerate(batch):
            # Add publish timestamp for latency tracking
            event["publish_timestamp"] = time.time()

            entry = {
                "Id": f"msg_{batch_idx}_{event_idx}",
                "MessageBody": json.dumps(event, separators=(',', ':')),
            }
            entries.append(entry)

        return self._send_batch_with_retry(entries, result)

    def _send_batch_with_retry(
        self, entries: List[Dict[str, Any]], result: PublishResult
    ) -> bool:
        """Send batch with exponential backoff retry logic."""
        max_retries = 3

        for attempt in range(max_retries + 1):
            try:
                response = self.sqs_client.send_message_batch(
                    QueueUrl=self.queue_url, Entries=entries
                )

                # Check for partial failures
                failed_messages = response.get("Failed", [])
                if failed_messages:
                    logger.warning(
                        "Batch partially failed: %d/%d messages failed",
                        len(failed_messages),
                        len(entries),
                    )
                    for failure in failed_messages:
                        logger.error(
                            "Message %s failed: %s - %s",
                            failure["Id"],
                            failure["Code"],
                            failure.get("Message", "Unknown error"),
                        )
                    return False

                logger.debug(
                    "Successfully published batch of %d messages", len(entries)
                )
                return True

            except (BotoCoreError, ClientError) as e:
                result.retries += 1

                if attempt < max_retries:
                    backoff_time = (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        "Batch publish failed (attempt %d/%d): %s. Retrying in %.2fs",
                        attempt + 1,
                        max_retries + 1,
                        e,
                        backoff_time,
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(
                        "Batch publish permanently failed after %d attempts: %s",
                        max_retries + 1,
                        e,
                    )
                    return False

        return False
