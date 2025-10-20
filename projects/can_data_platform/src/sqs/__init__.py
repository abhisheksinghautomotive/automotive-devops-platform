"""SQS package for AWS SQS operations in CAN data platform.

This package provides SQS queue management, configuration, and IAM policy
generation for the automotive DevOps platform CAN data processing pipeline.
"""

from .config import SQSQueueConfig
from .manager import SQSQueueManager
from .policy import sqs_consumer_policy, sqs_producer_policy

__all__ = [
    "SQSQueueConfig",
    "SQSQueueManager",
    "sqs_consumer_policy",
    "sqs_producer_policy",
]
