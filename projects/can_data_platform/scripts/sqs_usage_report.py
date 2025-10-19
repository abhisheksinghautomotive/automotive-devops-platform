"""SQS Usage & Health Check Script.

Fetches message counts and queue attributes for cost awareness.
"""

import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv


def setup_project_path():
    """Add project root to Python path for module imports."""
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# Setup path before any project imports (if needed in future)
setup_project_path()

load_dotenv()


def sqs_usage_report(sqs_queue_url):
    """Generate usage report for SQS queue showing message counts and timestamps."""
    client = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "us-east-1"))

    # Fetch attributes that affect cost/monitoring
    attrs = client.get_queue_attributes(
        QueueUrl=sqs_queue_url,
        AttributeNames=[
            'ApproximateNumberOfMessages',
            'ApproximateNumberOfMessagesNotVisible',
            'CreatedTimestamp',
            'LastModifiedTimestamp',
        ],
    )['Attributes']

    print(f"SQS Usage Report for {sqs_queue_url}")
    print(f"Approximate messages in queue: {attrs['ApproximateNumberOfMessages']}")
    print(
        f"Messages in flight (not visible): "
        f"{attrs['ApproximateNumberOfMessagesNotVisible']}"
    )
    print(f"Queue Created: {attrs['CreatedTimestamp']}")
    print(f"Last Modified: {attrs['LastModifiedTimestamp']}")


if __name__ == "__main__":
    queue_url = os.getenv("SQS_QUEUE_URL")
    if not queue_url:
        raise ValueError("SQS_QUEUE_URL not set. Add to .env.")
    sqs_usage_report(queue_url)
