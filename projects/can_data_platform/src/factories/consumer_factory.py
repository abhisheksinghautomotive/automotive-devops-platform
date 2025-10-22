"""Factory for creating SQS consumers with proper dependency injection."""

from ..consumers.sqs_consumer import SQSBatchConsumer
from ..consumers.interfaces import ConsumerInterface
from ..metrics.interfaces import LatencyTrackerInterface
from ..processors.interfaces import MessageProcessor


class SQSConsumerFactory:
    """Factory for creating SQS consumer instances."""

    @staticmethod
    def create_consumer(
        queue_url: str,
        aws_region: str,
        message_processor: MessageProcessor,
        latency_tracker: LatencyTrackerInterface,
        batch_size: int = 10,
        max_retries: int = 3,
        max_wait_time: int = 5,
    ) -> ConsumerInterface:
        """Create an SQS batch consumer instance.

        Args:
            queue_url: SQS queue URL
            aws_region: AWS region
            message_processor: Message processor instance
            latency_tracker: Latency tracker instance
            batch_size: Number of messages to process per batch
            max_retries: Maximum number of retry attempts
            max_wait_time: SQS long polling wait time in seconds

        Returns:
            ConsumerInterface instance
        """
        return SQSBatchConsumer(
            queue_url=queue_url,
            message_processor=message_processor,
            latency_tracker=latency_tracker,
            region_name=aws_region,
            batch_size=batch_size,
            max_retries=max_retries,
            max_wait_time=max_wait_time,
        )
