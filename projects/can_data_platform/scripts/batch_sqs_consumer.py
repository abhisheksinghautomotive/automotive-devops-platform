"""
SQS Batch Consumer for CAN Telemetry Platform.

Consumes messages from SQS in batches, processes each,
logs outcome, and deletes successfully processed messages.
"""
import time
import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
import boto3  # type: ignore
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
from dotenv import load_dotenv

load_dotenv()

# Clear previous log file when starting new execution
log_file = os.path.join(os.path.dirname(__file__), "..", "data", "batch_consumer.log")
if os.path.exists(log_file):
    os.remove(log_file)

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),  # This adds console output
    ],
)

QUEUE_URL = os.getenv("SQS_QUEUE_URL")
BATCH_SIZE = int(os.getenv("SQS_BATCH_SIZE", "10"))  # SQS max batch size is 10
POLL_INTERVAL = int(os.getenv("SQS_CONSUMER_POLL_SEC", "5"))  # Poll wait in seconds
MAX_RETRIES = int(os.getenv("SQS_DELETION_MAX_RETRIES", "3"))
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def process_message_body(message_body: str) -> bool:
    """Process a single SQS message body and return success status.

    Args:
        message_body: JSON string message body from SQS

    Returns:
        bool: True if processing succeeded, False otherwise
    """
    # Replace with real pipeline logic; currently logs the event and returns True
    try:
        event = json.loads(message_body)
        logging.info("Processing event: %s", event)
        # custom processing logic here
        return True
    except json.JSONDecodeError as e:
        logging.error("Could not process message: %s", e)
        return False


def receive_messages(sqs: Any) -> Optional[Dict[str, Any]]:
    """Receive a batch of messages from SQS with error handling.

    Args:
        sqs: Boto3 SQS client instance

    Returns:
        dict or None: SQS response dict or None if error occurred
    """
    try:
        return sqs.receive_message(  # type: ignore
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=BATCH_SIZE,
            WaitTimeSeconds=20,  # long polling
        )
    except (BotoCoreError, ClientError) as err:
        logging.error("Failed to receive batch: %s", err)
        return None


def delete_messages(sqs: Any, entries_to_delete: List[Dict[str, str]]) -> bool:
    """Delete successfully processed messages from SQS with retry logic.

    Args:
        sqs: Boto3 SQS client instance
        entries_to_delete: List of message deletion entries

    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = sqs.delete_message_batch(  # type: ignore
                QueueUrl=QUEUE_URL, Entries=entries_to_delete
            )
            deleted_count = len(result.get('Successful', []))  # type: ignore
            logging.info("Deleted %d messages", deleted_count)
            return True
        except (BotoCoreError, ClientError) as delete_err:
            logging.warning(
                "Attempt %d: Failed to delete batch: %s", attempt, delete_err
            )
            time.sleep(attempt * 2)
    return False


def process_batch(msgs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], int, int]:
    """Process a batch of SQS messages and prepare deletion entries.

    Args:
        msgs: List of SQS message objects

    Returns:
        tuple: (entries_to_delete, batch_success_count, batch_failure_count)
    """
    entries_to_delete: List[Dict[str, str]] = []
    batch_success = 0
    batch_failure = 0

    for msg in msgs:
        success = process_message_body(msg["Body"])
        if success:
            entries_to_delete.append(
                {"Id": msg["MessageId"], "ReceiptHandle": msg["ReceiptHandle"]}
            )
            batch_success += 1
        else:
            batch_failure += 1
    return entries_to_delete, batch_success, batch_failure


def batch_consume_sqs() -> None:
    """Consume SQS messages in batches continuously.

    Continuously polls SQS for messages, processes them, and deletes
    successfully processed messages. Includes error handling and
    graceful shutdown logic.
    """
    sqs = boto3.client('sqs', region_name=AWS_REGION)  # type: ignore
    consecutive_failures = 0
    while True:
        resp = receive_messages(sqs)
        if resp is None:
            consecutive_failures += 1
            if consecutive_failures > 5:
                logging.error("Consumer stopping due to consecutive failures.")
                break
            time.sleep(POLL_INTERVAL)
            continue

        consecutive_failures = 0
        msgs = resp.get("Messages", [])  # type: ignore
        if not msgs:
            logging.info("No messages in batch, sleeping...")
            print("⏳ No messages in queue, waiting...")
            time.sleep(POLL_INTERVAL)
            continue

        entries_to_delete, batch_success, batch_failure = process_batch(msgs)

        # Batch delete successfully processed messages
        if entries_to_delete:
            delete_messages(sqs, entries_to_delete)

        logging.info(
            "Batch processed: success=%d, failed=%d", batch_success, batch_failure
        )
        print(f"✅ Processed batch: {batch_success} success, {batch_failure} failed")

        # Sleep between polls to avoid hitting rate limits
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("🚀 Starting SQS Batch Consumer...")
    print(f"📡 Queue URL: {QUEUE_URL}")
    print(f"📦 Batch Size: {BATCH_SIZE}")
    print(f"⏱️  Poll Interval: {POLL_INTERVAL}s")
    print("Press Ctrl+C to stop\n")

    logging.info("Starting SQS Batch Consumer")
    batch_consume_sqs()
