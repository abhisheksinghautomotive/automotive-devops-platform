"""SQS IAM Policy templates module.

This module provides IAM policy templates for SQS queue access in the
automotive DevOps platform, following least-privilege security principles.
"""

from typing import Any, Dict


def sqs_producer_policy(queue_arn: str) -> Dict[str, Any]:
    """Generate IAM policy for SQS message producers.

    Creates an IAM policy that grants the minimum permissions needed
    to send messages to an SQS queue, following AWS security best practices.

    Args:
        queue_arn: ARN of the SQS queue to grant access to

    Returns:
        IAM policy document dictionary for SQS producers
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowSQSPublish",
                "Effect": "Allow",
                "Action": [
                    "sqs:SendMessage",
                    "sqs:GetQueueUrl",
                    "sqs:GetQueueAttributes",
                ],
                "Resource": queue_arn,
            }
        ],
    }


def sqs_consumer_policy(queue_arn: str) -> Dict[str, Any]:
    """Generate IAM policy for SQS message consumers.

    Creates an IAM policy that grants the minimum permissions needed
    to receive and delete messages from an SQS queue.

    Args:
        queue_arn: ARN of the SQS queue to grant access to

    Returns:
        IAM policy document dictionary for SQS consumers
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowSQSConsume",
                "Effect": "Allow",
                "Action": [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                ],
                "Resource": queue_arn,
            }
        ],
    }
