"""SQS batch consumer implementation with retry logic and error handling."""

import logging
import time
from typing import List, Dict, Any, Optional

import boto3  # type: ignore
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore

from .interfaces import ConsumerInterface, BatchConsumerResult
from ..processors.interfaces import MessageProcessor
from ..metrics.interfaces import LatencyTrackerInterface


logger = logging.getLogger(__name__)


class SQSBatchConsumer(ConsumerInterface):
    """SQS batch consumer following Single Responsibility Principle.

    Handles SQS message consumption, processing, and deletion with proper
    error handling.
    """

    def __init__(
        self,
        queue_url: str,
        message_processor: MessageProcessor,
        latency_tracker: LatencyTrackerInterface,
        region_name: str = "us-east-1",
        batch_size: int = 10,
        max_wait_time: int = 20,
        max_retries: int = 3,
    ):
        """Initialize SQS batch consumer.

        Args:
            queue_url: SQS queue URL
            message_processor: Message processor implementation
            latency_tracker: Latency tracker implementation
            region_name: AWS region name
            batch_size: Maximum messages per batch (1-10)
            max_wait_time: Long polling wait time in seconds
            max_retries: Maximum retry attempts for operations
        """
        if not queue_url:
            raise ValueError("Queue URL is required")

        self.queue_url = queue_url
        self.message_processor = message_processor
        self.latency_tracker = latency_tracker
        self.batch_size = min(max(batch_size, 1), 10)  # AWS SQS limitation
        self.max_wait_time = max_wait_time
        self.max_retries = max_retries

        self.sqs_client = boto3.client("sqs", region_name=region_name)
        self.consecutive_failures = 0
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def consume_batch(self) -> BatchConsumerResult:
        """Consume and process a batch of messages from SQS.

        Returns:
            BatchConsumerResult with processing statistics
        """
        start_time = time.perf_counter()

        try:
            # Receive messages from SQS with latency tracking
            sqs_start = time.perf_counter()
            response = self._receive_messages()
            sqs_end = time.perf_counter()
            self.latency_tracker.record_sqs_latency(sqs_start, sqs_end)

            if response is None:
                self.consecutive_failures += 1
                return BatchConsumerResult.create_empty()

            messages = response.get("Messages", [])
            if not messages:
                self.consecutive_failures = 0
                return BatchConsumerResult.create_empty()

            # Process messages with latency tracking
            processing_start = time.perf_counter()
            processing_results = self._process_messages(messages)
            processing_end = time.perf_counter()
            self.latency_tracker.record_batch_write_latency(
                processing_start, processing_end
            )

            # Delete successfully processed messages
            deletion_result = self._delete_successful_messages(
                messages, processing_results
            )
            deleted_count = deletion_result["deleted"]
            deletion_errors = deletion_result["errors"]

            # Calculate results
            consumed = len(messages)
            processed = len(processing_results)
            failed = processed - sum(1 for r in processing_results if r.success)
            processing_time = time.perf_counter() - start_time

            self.consecutive_failures = 0

            result = BatchConsumerResult(
                consumed=consumed,
                messages_processed=processed,
                messages_deleted=deleted_count,
                errors=failed,
                deletion_errors=deletion_errors,
                processing_time=processing_time,
            )

            self.logger.info(
                "Batch processed: %d consumed, %d processed, %d deleted, %d failed",
                consumed,
                processed,
                deleted_count,
                failed,
            )

            # Flush latency metrics only after deletions have been attempted
            try:
                should = getattr(self.latency_tracker, "should_flush", lambda: False)()
                if should:
                    self.latency_tracker.flush_metrics()
            except (AttributeError, ValueError, TypeError, RuntimeError):
                # Never let metric flushing break batch processing
                self.logger.warning("Latency tracker flush failed, continuing")

            return result

        except (BotoCoreError, ClientError, ValueError, TypeError, KeyError) as e:
            self.consecutive_failures += 1
            self.logger.error("Batch consumption failed: %s", e)
            return BatchConsumerResult.create_empty()

    def _receive_messages(self) -> Optional[Dict[str, Any]]:
        """Receive messages from SQS with error handling."""
        try:
            return self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=self.batch_size,
                WaitTimeSeconds=self.max_wait_time,
                AttributeNames=['SentTimestamp'],  # For queue age tracking
            )
        except (BotoCoreError, ClientError) as e:
            self.logger.error("Failed to receive messages: %s", e)
            return None

    def _process_messages(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """Process a list of SQS messages.

        Args:
            messages: List of SQS message dictionaries

        Returns:
            List of processing results
        """
        results = []

        for message in messages:
            try:
                message_body = message["Body"]
                result = self.message_processor.process_message(message_body)
                results.append(result)

                # Track end-to-end latency if event has timestamp
                # Use per-message processing time to get accurate E2E latency
                process_ts = time.time()
                if result.success and result.event_timestamp:
                    self.latency_tracker.record_e2e_latency(
                        result.event_timestamp, process_ts
                    )

                # Track queue age latency using SQS attributes
                if "Attributes" in message and "SentTimestamp" in message["Attributes"]:
                    self.latency_tracker.record_queue_age_latency(
                        message["Attributes"]["SentTimestamp"], process_ts
                    )

                # Step event counter for metrics
                self.latency_tracker.step_event()

                if result.success:
                    self.logger.debug("Message processed successfully")
                else:
                    self.logger.warning(
                        "Message processing failed: %s", result.error_message
                    )

            except (KeyError, ValueError, TypeError, AttributeError) as e:
                self.logger.error("Unexpected error processing message: %s", e)
                # Create a failure result for unexpected errors
                from ..processors.interfaces import ProcessingResult

                results.append(ProcessingResult.failure_result(str(e)))

        return results

    def _delete_successful_messages(
        self, messages: List[Dict[str, Any]], processing_results: List[Any]
    ) -> Dict[str, int]:
        """Delete messages that were processed successfully.

        Args:
            messages: Original SQS messages
            processing_results: Processing results for each message

        Returns:
            Dictionary with 'deleted' and 'errors' counts
        """
        # Build deletion entries for successful messages
        deletion_entries = []

        for message, result in zip(messages, processing_results):
            if result.success:
                deletion_entries.append(
                    {
                        "Id": message["MessageId"],
                        "ReceiptHandle": message["ReceiptHandle"],
                    }
                )

        if not deletion_entries:
            return {"deleted": 0, "errors": 0}

        # Delete messages with retry logic
        return self._delete_messages_with_retry(deletion_entries)

    def _delete_messages_with_retry(
        self, deletion_entries: List[Dict[str, str]]
    ) -> Dict[str, int]:
        """Delete messages with retry logic.

        Args:
            deletion_entries: List of message deletion entries

        Returns:
            Dictionary with 'deleted' and 'errors' counts
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.sqs_client.delete_message_batch(
                    QueueUrl=self.queue_url, Entries=deletion_entries
                )

                successful_deletions = response.get("Successful", [])
                failed_deletions = response.get("Failed", [])

                if failed_deletions:
                    self.logger.warning(
                        "Some message deletions failed: %d failed out of %d",
                        len(failed_deletions),
                        len(deletion_entries),
                    )
                    for failure in failed_deletions:
                        self.logger.error(
                            "Delete failed for message %s: %s",
                            failure["Id"],
                            failure.get("Message", "Unknown error"),
                        )

                deleted_count = len(successful_deletions)
                error_count = len(failed_deletions)
                self.logger.info("Successfully deleted %d messages", deleted_count)

                return {"deleted": deleted_count, "errors": error_count}

            except (BotoCoreError, ClientError) as e:
                if attempt < self.max_retries:
                    backoff_time = attempt * 2
                    self.logger.warning(
                        "Message deletion failed (attempt %d/%d): %s. Retrying in %ds",
                        attempt,
                        self.max_retries,
                        e,
                        backoff_time,
                    )
                    time.sleep(backoff_time)
                else:
                    self.logger.error(
                        "Message deletion permanently failed after %d attempts: %s",
                        self.max_retries,
                        e,
                    )

        # If all retries failed, return error count equal to deletion entries
        return {"deleted": 0, "errors": len(deletion_entries)}

    def is_healthy(self) -> bool:
        """Check if the consumer is in a healthy state.

        Returns:
            True if consumer is healthy (< 5 consecutive failures), False otherwise
        """
        return self.consecutive_failures < 5

    def health_check(self) -> bool:
        """Alias for is_healthy method to match expected interface.

        Returns:
            True if consumer is healthy, False otherwise
        """
        return self.is_healthy()

    def close(self) -> None:
        """Clean up consumer resources."""
        # boto3 clients don't need explicit cleanup
        self.logger.info("SQS consumer closed")


class SQSConsumerFactory:
    """Factory for creating SQS consumers."""

    @staticmethod
    def create_batch_consumer(
        queue_url: str, message_processor: MessageProcessor, **kwargs
    ) -> SQSBatchConsumer:
        """Create an SQS batch consumer with specified processor.

        Args:
            queue_url: SQS queue URL
            message_processor: Message processor implementation
            **kwargs: Additional consumer configuration

        Returns:
            Configured SQSBatchConsumer instance
        """
        return SQSBatchConsumer(
            queue_url=queue_url, message_processor=message_processor, **kwargs
        )
