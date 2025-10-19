"""SQS Queue Manager module.

This module provides the SQSQueueManager class for creating and managing
AWS SQS queues in the automotive DevOps platform CAN data processing pipeline.
"""

import json
from typing import Dict, Any, Optional

import boto3

from .config import SQSQueueConfig


class SQSQueueManager:
    """Manager class for AWS SQS queue operations.

    This class handles SQS queue creation, message sending, and message receiving
    for the CAN data platform with proper AWS session management.

    Attributes:
        sqs: Boto3 SQS client instance
        config: SQS queue configuration settings
    """

    def __init__(self, config: SQSQueueConfig, profile: Optional[str] = None):
        """Initialize SQS Queue Manager.

        Args:
            config: SQS queue configuration instance
            profile: AWS profile name for credentials (optional)
        """
        session_kwargs = {"region_name": config.region}
        if profile:
            session_kwargs["profile_name"] = profile
        self.sqs = boto3.Session(**session_kwargs).client("sqs")
        self.config = config

    def create_queue(self) -> str:
        """Create SQS queue with configured attributes.

        Returns:
            Queue URL string for the created queue
        """
        attrs = {
            "MessageRetentionPeriod": str(self.config.message_retention_seconds),
            "VisibilityTimeout": str(self.config.visibility_timeout),
            "MaximumMessageSize": str(self.config.max_message_size),
            "ReceiveMessageWaitTimeSeconds": str(self.config.wait_time_seconds),
        }
        if self.config.encrypt:
            attrs["SqsManagedSseEnabled"] = "true"
        resp = self.sqs.create_queue(QueueName=self.config.queue_name, Attributes=attrs)
        return resp["QueueUrl"]

    def send_test_message(
        self, queue_url: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send test message to SQS queue.

        Args:
            queue_url: SQS queue URL
            payload: Message payload dictionary

        Returns:
            SQS send_message response containing MessageId
        """
        return self.sqs.send_message(
            QueueUrl=queue_url, MessageBody=json.dumps(payload)
        )

    def receive_test_message(self, queue_url: str) -> Dict[str, Any]:
        """Receive test message from SQS queue.

        Args:
            queue_url: SQS queue URL

        Returns:
            SQS receive_message response
        """
        return self.sqs.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20
        )
