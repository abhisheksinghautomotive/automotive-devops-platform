"""SQS Queue Configuration module.

This module provides configuration classes for AWS SQS queue management
in the automotive DevOps platform CAN data processing pipeline.
"""

from dataclasses import dataclass


@dataclass
class SQSQueueConfig:
    """Configuration class for AWS SQS queue settings.

    This class encapsulates all configuration parameters needed to create
    and manage SQS queues for the CAN data platform, including timeout
    settings, message retention, and encryption options.

    Attributes:
        queue_name: Name of the SQS queue to create/manage
        message_retention_seconds: How long messages are retained (default: 4 days)
        visibility_timeout: Timeout for message visibility after receive
        wait_time_seconds: Long polling wait time to reduce empty receives
        max_message_size: Maximum size allowed for messages in bytes
        region: AWS region for queue creation
        encrypt: Whether to enable server-side encryption
    """

    queue_name: str
    message_retention_seconds: int = 345600  # 4 days
    visibility_timeout: int = 30
    wait_time_seconds: int = 20
    max_message_size: int = 262144  # 256 KB
    region: str = "us-east-1"
    encrypt: bool = False
