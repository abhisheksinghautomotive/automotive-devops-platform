#!/usr/bin/env python3
"""SQS Queue Setup Script.

This script sets up AWS SQS queues for the automotive DevOps platform
CAN data processing pipeline with optional IAM policy generation.

Usage:
    python setup_sqs.py --queue-name my-can-data-queue
    python setup_sqs.py --queue-name my-queue --region us-west-2 --encrypt
    python setup_sqs.py --queue-name my-queue --output-iam
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def setup_project_path():
    """Add project root to Python path for module imports."""
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# Setup path before importing project modules
setup_project_path()

from projects.can_data_platform.src.sqs.config import SQSQueueConfig  # noqa: E402
from projects.can_data_platform.src.sqs.manager import SQSQueueManager  # noqa: E402
from projects.can_data_platform.src.sqs.policy import (  # noqa: E402
    sqs_producer_policy,
    sqs_consumer_policy,
)

load_dotenv()


def main() -> None:
    """Set up SQS Queue for CAN Data Platform."""
    parser = argparse.ArgumentParser(
        description="Setup SQS Queue for CAN Data Platform"
    )
    parser.add_argument(
        "--queue-name", default=os.getenv("SQS_QUEUE_NAME"), required=True
    )
    parser.add_argument("--region", default=os.getenv("AWS_REGION"))
    parser.add_argument("--encrypt", action="store_true")
    parser.add_argument("--profile", default=os.getenv("AWS_PROFILE"))
    parser.add_argument(
        "--output-iam", action="store_true", help="Output IAM policy files"
    )
    args = parser.parse_args()

    # 1. Build config from arguments
    config_kwargs = {'queue_name': args.queue_name, 'encrypt': args.encrypt}
    if args.region is not None:
        config_kwargs['region'] = args.region

    config = SQSQueueConfig(**config_kwargs)
    manager = SQSQueueManager(config, profile=args.profile)

    # 2. Create the queue and print info
    queue_url = manager.create_queue()
    print(f"Queue created at: {queue_url}")

    # 3. Generate policies if requested
    if args.output_iam:
        try:
            queue_arn_response = manager.sqs.get_queue_attributes(  # type: ignore
                QueueUrl=queue_url, AttributeNames=['QueueArn']
            )
            queue_arn: str = str(  # type: ignore
                queue_arn_response['Attributes']['QueueArn']  # type: ignore
            )
        except (KeyError, ValueError) as e:
            print(f"Error getting queue ARN: {e}")
            return

        # Create policies in the data directory
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)

        producer_policy_path = data_dir / 'sqs-producer-policy.json'
        consumer_policy_path = data_dir / 'sqs-consumer-policy.json'

        with open(producer_policy_path, 'w', encoding='utf-8') as f:
            json.dump(sqs_producer_policy(queue_arn), f, indent=2)

        with open(consumer_policy_path, 'w', encoding='utf-8') as f:
            json.dump(sqs_consumer_policy(queue_arn), f, indent=2)

        print(f"IAM policies written to {data_dir}:")
        print(f"  - {producer_policy_path}")
        print(f"  - {consumer_policy_path}")


if __name__ == "__main__":
    main()
