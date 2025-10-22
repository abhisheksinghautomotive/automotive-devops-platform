"""Concurrent SQS consumer for meeting strict SLA requirements."""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Union

import boto3  # type: ignore
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore

from ..metrics.interfaces import LatencyTrackerInterface


logger = logging.getLogger(__name__)


class ConcurrentSQSConsumer:
    """High-performance concurrent SQS consumer for strict SLA requirements.

    Features:
    - Concurrent message processing with thread pools
    - Aggressive polling with reduced intervals
    - Batch prefetching for reduced latency
    - SLA-aware processing prioritization
    """

    def __init__(
        self,
        queue_url: str,
        processor: Any,  # Message processor implementation
        latency_tracker: LatencyTrackerInterface,
        max_workers: int = 4,
        poll_interval: float = 0.1,  # Aggressive 100ms polling
        batch_size: int = 10,
        max_retries: int = 3,
        sla_threshold_seconds: float = 5.0,
    ):
        """Initialize concurrent SQS consumer.

        Args:
            queue_url: SQS queue URL
            processor: Message processor implementation
            latency_tracker: Latency tracking implementation
            max_workers: Maximum concurrent processing threads
            poll_interval: Polling interval in seconds (reduced for SLA)
            batch_size: Messages per batch
            max_retries: Maximum retry attempts
            sla_threshold_seconds: SLA threshold for prioritization
        """
        self.queue_url = queue_url
        self.processor = processor
        self.latency_tracker = latency_tracker
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.sla_threshold_seconds = sla_threshold_seconds

        # AWS SQS client
        self.sqs = boto3.client('sqs')

        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Processing state
        self.running = False
        self.processed_count = 0
        self.error_count = 0

        logger.info(
            "ConcurrentSQSConsumer initialized: workers=%d, poll_interval=%.1fms, "
            "sla=%.1fs",
            max_workers,
            poll_interval * 1000,
            sla_threshold_seconds,
        )

    async def start_consuming(self) -> Dict[str, Union[int, float]]:
        """Start concurrent message consumption with SLA monitoring.

        Returns:
            Statistics dictionary with processing results
        """
        self.running = True
        logger.info("Starting concurrent SQS consumption...")

        try:
            while self.running:
                # Fetch batch of messages
                poll_start = time.time()
                messages = self._fetch_messages()
                poll_end = time.time()

                if messages:
                    # Record SQS polling latency
                    self.latency_tracker.record_sqs_latency(poll_start, poll_end)

                    # Process messages concurrently
                    await self._process_messages_concurrent(messages)
                else:
                    # Short sleep to avoid overwhelming SQS
                    await asyncio.sleep(self.poll_interval)

        except Exception as e:
            logger.error("Error in concurrent consumption: %s", e)
            raise
        finally:
            self.executor.shutdown(wait=True)
            logger.info("Concurrent consumer shutdown complete")

        total_processed = self.processed_count + self.error_count
        success_rate = (self.processed_count / max(1, total_processed)) * 100

        return {
            "processed": self.processed_count,
            "errors": self.error_count,
            "success_rate": success_rate,
        }

    def _fetch_messages(self) -> List[Dict]:
        """Fetch messages from SQS with error handling."""
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=self.batch_size,
                WaitTimeSeconds=0,  # No long polling for aggressive latency
                MessageAttributeNames=['All'],
            )

            messages = response.get('Messages', [])
            logger.debug("Fetched %d messages from SQS", len(messages))
            return messages

        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to fetch messages from SQS: %s", e)
            return []

    async def _process_messages_concurrent(self, messages: List[Dict]) -> None:
        """Process messages concurrently with SLA prioritization."""
        batch_start = time.time()

        # Create processing tasks
        tasks = []
        for message in messages:
            task = asyncio.create_task(self._process_single_message(message))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_end = time.time()
        self.latency_tracker.record_batch_write_latency(batch_start, batch_end)

        # Process results
        successful_receipts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Error processing message: %s", result)
                self.error_count += 1
            else:
                successful_receipts.append(messages[i]['ReceiptHandle'])
                self.processed_count += 1

        # Delete successfully processed messages
        if successful_receipts:
            self._delete_messages(successful_receipts)

        logger.info(
            "Concurrent batch: %d processed, %d errors, %.2fms processing time",
            len(successful_receipts),
            len(results) - len(successful_receipts),
            (batch_end - batch_start) * 1000,
        )

    async def _process_single_message(self, message: Dict) -> bool:
        """Process a single message with SLA tracking."""
        try:
            # Get original message body string for processor
            message_body = message['Body']

            # Parse message body for timestamp extraction
            body = json.loads(message_body)
            process_timestamp = time.time()

            # Extract event timestamp for E2E latency
            event_timestamp = body.get('timestamp', process_timestamp)

            # Check SLA urgency
            e2e_latency = process_timestamp - event_timestamp
            if e2e_latency > self.sla_threshold_seconds:
                logger.warning(
                    "SLA violation detected: E2E latency %.2fs exceeds threshold %.1fs",
                    e2e_latency,
                    self.sla_threshold_seconds,
                )

            # Process message with original JSON string
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.processor.process_message, message_body
            )

            # Record E2E latency
            self.latency_tracker.record_e2e_latency(event_timestamp, process_timestamp)
            self.latency_tracker.step_event()

            return True

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to process message: %s", e)
            return False

    def _delete_messages(self, receipt_handles: List[str]) -> None:
        """Delete successfully processed messages from SQS."""
        try:
            # Batch delete (up to 10 messages per request)
            for i in range(0, len(receipt_handles), 10):
                batch_receipts = receipt_handles[i : i + 10]
                entries = [
                    {'Id': str(j), 'ReceiptHandle': receipt}
                    for j, receipt in enumerate(batch_receipts)
                ]

                self.sqs.delete_message_batch(QueueUrl=self.queue_url, Entries=entries)

            logger.debug("Deleted %d messages from SQS", len(receipt_handles))

        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to delete messages from SQS: %s", e)

    def stop(self) -> None:
        """Stop the concurrent consumer."""
        self.running = False
        logger.info("Stopping concurrent consumer...")
