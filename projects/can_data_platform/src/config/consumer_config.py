"""Consumer configuration management."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class ConsumerConfig:
    """Configuration for SQS batch consumer following Data Transfer Object pattern."""

    # SQS Configuration
    queue_url: str
    batch_size: int
    poll_interval: float
    max_retries: int
    max_wait_time: int
    aws_region: str

    # Latency Tracking Configuration
    latency_flush_every: int
    latency_output_dir: Optional[str]
    sla_threshold_seconds: float

    # Logging Configuration
    log_file: Optional[str]
    log_level: str

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid
        """
        if not self.queue_url:
            raise ValueError("SQS queue URL is required")

        if not 1 <= self.batch_size <= 10:
            raise ValueError("Batch size must be between 1 and 10")

        if self.poll_interval < 0:
            raise ValueError("Poll interval cannot be negative")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

        if self.latency_flush_every < 1:
            raise ValueError("Latency flush interval must be at least 1")

        if self.sla_threshold_seconds <= 0:
            raise ValueError("SLA threshold must be positive")


class ConsumerConfigManager:
    """Configuration manager for consumer application.

    Follows Single Responsibility Principle by focusing only on configuration loading.
    """

    # Default values
    DEFAULT_BATCH_SIZE = 10
    DEFAULT_POLL_INTERVAL = 0.3
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_MAX_WAIT_TIME = 5
    DEFAULT_AWS_REGION = "us-east-1"
    DEFAULT_LATENCY_FLUSH_EVERY = 100
    DEFAULT_SLA_THRESHOLD = 5.0
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LATENCY_OUTPUT_DIR = "projects/can_data_platform/data/metrics"
    # Enable latency tracking by default

    def __init__(self, load_env: bool = True):
        """Initialize configuration manager.

        Args:
            load_env: Whether to load environment variables from .env file
        """
        if load_env:
            load_dotenv()

    def load_config(self, **overrides) -> ConsumerConfig:
        """Load consumer configuration from environment variables with overrides.

        Args:
            **overrides: Configuration overrides

        Returns:
            ConsumerConfig instance

        Raises:
            ValueError: If configuration validation fails
        """
        config = ConsumerConfig(
            # SQS Configuration
            queue_url=overrides.get("queue_url", os.getenv("SQS_QUEUE_URL", "")),
            batch_size=overrides.get(
                "batch_size",
                int(os.getenv("SQS_BATCH_SIZE", str(self.DEFAULT_BATCH_SIZE))),
            ),
            poll_interval=overrides.get(
                "poll_interval",
                float(
                    os.getenv("SQS_CONSUMER_POLL_SEC", str(self.DEFAULT_POLL_INTERVAL))
                ),
            ),
            max_retries=overrides.get(
                "max_retries",
                int(
                    os.getenv("SQS_DELETION_MAX_RETRIES", str(self.DEFAULT_MAX_RETRIES))
                ),
            ),
            max_wait_time=overrides.get(
                "max_wait_time",
                int(
                    os.getenv("SQS_WAIT_TIME_SECONDS", str(self.DEFAULT_MAX_WAIT_TIME))
                ),
            ),
            aws_region=overrides.get(
                "aws_region", os.getenv("AWS_REGION", self.DEFAULT_AWS_REGION)
            ),
            # Latency Tracking Configuration
            latency_flush_every=overrides.get(
                "latency_flush_every",
                int(
                    os.getenv(
                        "LATENCY_FLUSH_EVERY", str(self.DEFAULT_LATENCY_FLUSH_EVERY)
                    )
                ),
            ),
            latency_output_dir=overrides.get(
                "latency_output_dir",
                os.getenv("LATENCY_OUTPUT_DIR", self.DEFAULT_LATENCY_OUTPUT_DIR),
            ),
            sla_threshold_seconds=overrides.get(
                "sla_threshold_seconds",
                float(
                    os.getenv("SLA_THRESHOLD_SECONDS", str(self.DEFAULT_SLA_THRESHOLD))
                ),
            ),
            # Logging Configuration
            log_file=overrides.get("log_file", os.getenv("CONSUMER_LOG_FILE")),
            log_level=overrides.get(
                "log_level", os.getenv("LOG_LEVEL", self.DEFAULT_LOG_LEVEL)
            ),
        )

        # Validate configuration
        config.validate()

        return config

    @staticmethod
    def create_from_args(args) -> ConsumerConfig:
        """Create configuration from command-line arguments.

        Args:
            args: argparse.Namespace object

        Returns:
            ConsumerConfig instance
        """
        manager = ConsumerConfigManager()

        overrides = {}

        # Override with command-line arguments if provided
        if hasattr(args, 'batch_size') and args.batch_size is not None:
            overrides['batch_size'] = args.batch_size

        if hasattr(args, 'poll_interval') and args.poll_interval is not None:
            overrides['poll_interval'] = args.poll_interval

        if hasattr(args, 'max_retries') and args.max_retries is not None:
            overrides['max_retries'] = args.max_retries

        if hasattr(args, 'log_level') and args.log_level is not None:
            overrides['log_level'] = args.log_level.upper()

        if hasattr(args, 'latency_flush') and args.latency_flush is not None:
            overrides['latency_flush_every'] = args.latency_flush

        return manager.load_config(**overrides)
