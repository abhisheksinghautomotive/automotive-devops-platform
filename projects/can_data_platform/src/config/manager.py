"""Configuration manager for telemetry application."""

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from dotenv import load_dotenv


@dataclass
class TelemetryConfig:
    """Configuration data class following Data Transfer Object pattern."""

    # SQS Configuration
    sqs_queue_url: Optional[str]
    aws_region: str
    sqs_batch_size: int
    stream_interval: float

    # Event Generation Configuration
    num_modules: int
    voltage_range: Tuple[int, int]
    offset_range: Tuple[int, int]

    # Output Configuration
    default_output_path: str

    def validate(self) -> None:
        """Validate configuration values."""
        if self.sqs_batch_size > 10:
            raise ValueError("SQS batch size cannot exceed 10 (AWS limitation)")

        if self.sqs_batch_size < 1:
            raise ValueError("SQS batch size must be at least 1")

        if self.stream_interval < 0:
            raise ValueError("Stream interval cannot be negative")

        if self.num_modules < 1:
            raise ValueError("Number of modules must be at least 1")


class ConfigManager:
    """Configuration manager following Single Responsibility Principle.

    Handles loading and validating configuration from environment variables.
    """

    # Default values
    DEFAULT_AWS_REGION = "us-east-1"
    DEFAULT_SQS_BATCH_SIZE = 10
    DEFAULT_STREAM_INTERVAL = 0.05
    DEFAULT_NUM_MODULES = 4
    DEFAULT_VOLTAGE_RANGE = (3400, 4150)
    DEFAULT_OFFSET_RANGE = (-40, 40)

    def __init__(self, load_env: bool = True):
        """Initialize configuration manager.

        Args:
            load_env: Whether to load environment variables from .env file
        """
        if load_env:
            load_dotenv()

    def load_config(self, **overrides) -> TelemetryConfig:
        """Load configuration from environment variables with optional overrides.

        Args:
            **overrides: Configuration overrides

        Returns:
            TelemetryConfig instance

        Raises:
            ValueError: If configuration validation fails
        """
        config = TelemetryConfig(
            # SQS Configuration
            sqs_queue_url=overrides.get("sqs_queue_url", os.getenv("SQS_QUEUE_URL")),
            aws_region=overrides.get(
                "aws_region", os.getenv("AWS_REGION", self.DEFAULT_AWS_REGION)
            ),
            sqs_batch_size=overrides.get(
                "sqs_batch_size",
                int(os.getenv("SQS_BATCH_SIZE", str(self.DEFAULT_SQS_BATCH_SIZE))),
            ),
            stream_interval=overrides.get(
                "stream_interval",
                float(
                    os.getenv(
                        "PRODUCER_STREAM_INTERVAL",
                        os.getenv("STREAM_INTERVAL", str(self.DEFAULT_STREAM_INTERVAL)),
                    )
                ),
            ),
            # Event Generation Configuration
            num_modules=overrides.get("num_modules", self.DEFAULT_NUM_MODULES),
            voltage_range=overrides.get("voltage_range", self.DEFAULT_VOLTAGE_RANGE),
            offset_range=overrides.get("offset_range", self.DEFAULT_OFFSET_RANGE),
            # Output Configuration
            default_output_path=overrides.get(
                "default_output_path",
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "data",
                    "sample_events_optimized.jsonl",
                ),
            ),
        )

        # Validate configuration
        config.validate()

        return config

    @staticmethod
    def create_from_args(args) -> TelemetryConfig:
        """Create configuration from command-line arguments.

        Args:
            args: argparse.Namespace object

        Returns:
            TelemetryConfig instance
        """
        manager = ConfigManager()

        overrides = {}
        if hasattr(args, 'stream_interval') and args.stream_interval is not None:
            overrides['stream_interval'] = args.stream_interval

        if hasattr(args, 'batch_size') and args.batch_size is not None:
            overrides['sqs_batch_size'] = min(args.batch_size, 10)

        if hasattr(args, 'output') and args.output is not None:
            overrides['default_output_path'] = args.output

        return manager.load_config(**overrides)
