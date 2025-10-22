"""Consumer application orchestrator with dependency injection."""

import argparse
import logging
import signal
import sys
import time

from ..config.consumer_config import ConsumerConfig, ConsumerConfigManager
from ..factories.consumer_factory import SQSConsumerFactory
from ..factories.latency_factory import LatencyTrackerFactory
from ..factories.processor_factory import MessageProcessorFactory


class ConsumerApp:
    """Consumer application orchestrator.

    Follows Dependency Inversion Principle by depending on abstractions.
    Orchestrates the entire consumer pipeline with proper dependency injection.
    """

    def __init__(self, config: ConsumerConfig):
        """Initialize consumer application.

        Args:
            config: Consumer configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        self._running = False

        # Add total message tracking
        self.total_stats = {
            "messages_consumed": 0,
            "messages_processed": 0,
            "messages_deleted": 0,
            "total_errors": 0,
            "total_deletion_errors": 0,
            "batches_processed": 0,
        }

        # Track consecutive empty batches for user guidance
        self.consecutive_empty_batches = 0
        self.max_empty_before_suggestion = 3

        # Dependency injection - create components through factories
        self.latency_tracker = LatencyTrackerFactory.create_tracker(
            enabled=config.latency_output_dir is not None,
            output_dir=config.latency_output_dir,
            flush_every=config.latency_flush_every,
            sla_threshold_seconds=config.sla_threshold_seconds,
        )

        self.message_processor = MessageProcessorFactory.create_processor(
            processor_type="telemetry"
        )

        self.consumer = SQSConsumerFactory.create_consumer(
            queue_url=config.queue_url,
            aws_region=config.aws_region,
            message_processor=self.message_processor,
            latency_tracker=self.latency_tracker,
            batch_size=config.batch_size,
            max_retries=config.max_retries,
            max_wait_time=config.max_wait_time,
        )

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration.

        Returns:
            Configured logger instance
        """
        # Create logger
        logger = logging.getLogger("consumer_app")
        logger.setLevel(getattr(logging, self.config.log_level))

        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler if specified
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info("Received signal %s, initiating graceful shutdown...", signum)
        self._running = False

    def run(self) -> None:
        """Run the consumer application with proper error handling."""
        self._initialize_consumer()
        self._running = True

        try:
            self._main_processing_loop()
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error("Critical error in consumer application: %s", e)
            raise
        finally:
            self._shutdown()

    def _initialize_consumer(self) -> None:
        """Initialize and log consumer configuration."""
        self.logger.info("Starting SQS batch consumer application...")
        self.logger.info("Queue URL: %s", self.config.queue_url)
        self.logger.info("Batch size: %s", self.config.batch_size)
        self.logger.info("Poll interval: %s seconds", self.config.poll_interval)
        self.logger.info("Max retries: %s", self.config.max_retries)

        if self.config.latency_output_dir:
            self.logger.info(
                "Latency tracking enabled, output: %s", self.config.latency_output_dir
            )
        else:
            self.logger.info("Latency tracking disabled")

    def _main_processing_loop(self) -> None:
        """Process messages continuously with optimized polling."""
        while self._running:
            try:
                result = self._process_batch()
                # Only sleep if no messages were processed (queue is empty)
                if self._running and result.messages_processed == 0:
                    time.sleep(self.config.poll_interval)
                # If messages were processed, immediately poll again for more
            except (ConnectionError, TimeoutError, ValueError) as e:
                self.logger.error("Error during message processing: %s", e)
                if self._running:
                    time.sleep(self.config.poll_interval)

    def _process_batch(self):
        """Process a single batch of messages and return the result."""
        result = self.consumer.consume_batch()
        self._update_statistics(result)
        self._handle_batch_result(result)
        self._check_consumer_health()
        return result

    def _update_statistics(self, result) -> None:
        """Update total statistics with batch result."""
        self.total_stats["messages_consumed"] += result.consumed
        self.total_stats["messages_processed"] += result.messages_processed
        self.total_stats["messages_deleted"] += result.messages_deleted
        self.total_stats["total_errors"] += result.errors
        self.total_stats["total_deletion_errors"] += result.deletion_errors
        self.total_stats["batches_processed"] += 1

    def _handle_batch_result(self, result) -> None:
        """Handle the result of batch processing and logging."""
        if result.messages_processed > 0:
            self._handle_successful_batch(result)
        else:
            self._handle_empty_batch()

        self._log_batch_errors(result)

    def _handle_successful_batch(self, result) -> None:
        """Handle a batch with processed messages."""
        self.consecutive_empty_batches = 0
        self.logger.info(
            "Batch: %s processed, %s errors, %s deleted | "
            "Total: %s processed, %s deleted",
            result.messages_processed,
            result.errors,
            result.messages_deleted,
            self.total_stats['messages_processed'],
            self.total_stats['messages_deleted'],
        )

    def _handle_empty_batch(self) -> None:
        """Handle a batch with no processed messages."""
        self.consecutive_empty_batches += 1

        if self.consecutive_empty_batches == 1:
            self.logger.info("No messages found in queue")
        elif self.consecutive_empty_batches >= self.max_empty_before_suggestion:
            self.logger.info(
                "No messages found for %s consecutive polls. "
                "Queue appears to be empty. "
                "Consider shutting down with Ctrl+C.",
                self.consecutive_empty_batches,
            )

    def _log_batch_errors(self, result) -> None:
        """Log any errors encountered during batch processing."""
        if result.errors > 0:
            self.logger.warning("Encountered %s processing errors", result.errors)
        if result.deletion_errors > 0:
            self.logger.warning(
                "Encountered %s deletion errors", result.deletion_errors
            )

    def _check_consumer_health(self) -> None:
        """Check consumer health and stop if unhealthy."""
        if not self.consumer.health_check():
            self.logger.error("Consumer health check failed")
            self._running = False

    def _shutdown(self) -> None:
        """Perform graceful shutdown of all components."""
        self.logger.info("Shutting down consumer application...")

        # Flush latency metrics
        try:
            self.latency_tracker.flush()
            self.logger.info("Flushed latency metrics")
        except (IOError, OSError) as e:
            self.logger.error("Error flushing latency metrics: %s", e)
        self.logger.info("Consumer application shutdown complete")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="SQS Batch Consumer for CAN Data Platform",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of messages to process in each batch (1-10)",
    )

    parser.add_argument(
        "--poll-interval",
        type=float,
        help="Seconds to wait between polling SQS for messages",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        help="Maximum number of retries for failed operations",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )

    parser.add_argument(
        "--latency-flush",
        type=int,
        help="Number of measurements before flushing latency metrics",
    )

    return parser


def main() -> None:
    """Start the consumer application with command-line arguments."""
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Load configuration
        config = ConsumerConfigManager.create_from_args(args)

        # Create and run application
        app = ConsumerApp(config)
        app.run()

    except (ValueError, FileNotFoundError, ConnectionError) as e:
        print(f"Failed to start consumer application: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
