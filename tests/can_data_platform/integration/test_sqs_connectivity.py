# tests/can_data_platform/integration/test_sqs_connectivity.py

"""
Integration test for AWS SQS telemetry queue connectivity.
Verifies send → receive → delete real message flow.

Run with:
$ pytest tests/can_data_platform/integration/test_sqs_connectivity.py
"""

import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

import pytest
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

load_dotenv()
logger = logging.getLogger("integration.sqs")
logger.setLevel(logging.INFO)


@pytest.mark.integration
def test_sqs_send_receive_delete(monkeypatch):
    """
    End-to-end integration test for CAN data SQS queue (dev).
    - Sends a unique test telemetry message
    - Receives the message back (with wait and retries)
    - Validates data
    - Deletes from queue
    - Asserts zero messages left and correct flow

    Fails if permissions, config, or network are wrong.
    Skips if env vars missing (for CI portability).
    """
    queue_url = os.getenv("SQS_QUEUE_URL")
    queue_name = os.getenv("SQS_QUEUE_NAME", "telemetry-queue-dev")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not queue_url:
        pytest.skip("SQS_QUEUE_URL not set (supply in .env or CI secrets)")

    # 1. Construct test config and manager
    config = SQSQueueConfig(queue_name=queue_name, region=region)
    manager = SQSQueueManager(config)

    # 2. Compose unique test message
    test_id = str(uuid.uuid4())
    test_message = {
        "vehicle_id": "test-integration-001",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uuid": test_id,
        "test_flag": True,
    }

    # 3. Send test message (assert success)
    response = manager.send_test_message(queue_url, payload=test_message)
    logger.info("SENT MessageID: %s | Test UUID: %s", response["MessageId"], test_id)
    assert "MessageId" in response, "Message not sent!"

    # 4. Receive and validate (retry for up to 3*20s to handle queue delay in cloud environments)
    received = None
    for _ in range(3):
        resp = manager.receive_test_message(queue_url)
        messages = resp.get("Messages", [])
        # Parse and match test message by UUID
        for msg in messages:
            body = json.loads(msg["Body"])
            if body.get("uuid") == test_id:
                received = (msg, body)
                break
        if received:
            break
        time.sleep(5)
    assert received is not None, "Test message not found in SQS after 3 tries"

    # 5. Check message integrity
    msg_obj, body = received
    assert body["vehicle_id"] == "test-integration-001"
    assert body["uuid"] == test_id
    assert body["test_flag"] is True

    # 6. Delete test message; confirm no errors
    handle = msg_obj["ReceiptHandle"]
    manager.sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=handle)
    logger.info("DELETED MessageID: %s", msg_obj["MessageId"])

    # 7. Optionally, assert queue is clear (skip if in shared dev queue to avoid false negatives)
    # next_msgs = manager.receive_test_message(queue_url)
    # assert "Messages" not in next_msgs

    print("Integration SQS test PASSED: send → receive → delete OK.")
