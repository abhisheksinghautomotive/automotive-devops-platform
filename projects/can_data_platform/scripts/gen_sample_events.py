"""Module to generate sample battery cell events (with module-to-module variance).

This module provides functionality to generate sample battery cell events
and publish to SQS, file, or both.
"""

import argparse
import json
import random
import time
import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import boto3
from botocore.exceptions import BotoCoreError, ClientError

load_dotenv()
logger = logging.getLogger("gen_sample_events")
logger.setLevel(logging.INFO)


def generate_events(
    num_events: int, num_modules: int = 4, offset_range: tuple = (-40, 40)
) -> List[Dict[str, Any]]:
    """Generate sample battery events with module-to-module voltage variance."""
    module_offsets: List[int] = [
        random.randint(*offset_range) for _ in range(num_modules)
    ]
    events: List[Dict[str, Any]] = []
    for _ in range(num_events):
        module_voltages: List[int] = []
        for idx in range(num_modules):
            base_voltage = random.randint(3400, 4150)
            noisy_voltage = base_voltage + module_offsets[idx]
            module_voltages.append(noisy_voltage)
        # Create dynamic cell voltage fields based on actual num_modules
        event: Dict[str, Any] = {}
        for i, voltage in enumerate(module_voltages):
            event[f"Cell{i+1}Voltage"] = voltage

        event.update(
            {
                "min_voltage": min(module_voltages),
                "max_voltage": max(module_voltages),
                "avg_voltage": round(sum(module_voltages) / num_modules),
                "module_offsets": list(module_offsets),
            }
        )
        events.append(event)
    return events


def publish_to_sqs(
    events: List[Dict[str, Any]], queue_url: str, max_retries: int = 3
) -> None:
    """Publish events to SQS with retry and metrics logging."""
    sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "us-east-1"))
    successes = 0
    failures = 0
    for event in events:
        payload = json.dumps(event)
        attempt = 0
        while attempt < max_retries:
            try:
                sqs.send_message(QueueUrl=queue_url, MessageBody=payload)
                successes += 1
                break
            except (BotoCoreError, ClientError) as e:
                attempt += 1
                backoff = (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    "Publish failed (attempt %d): %s. Retrying in %.1fs.",
                    attempt,
                    e,
                    backoff,
                )
                time.sleep(backoff)
        else:
            failures += 1
            logger.error("Publish permanently failed for event: {%s}", payload)
    logger.info("Published %d events to SQS, %d failures.", successes, failures)
    print(f"SQS publish: Success {successes}, Failures {failures}")


def write_events_to_file(events: List[Dict[str, Any]], output_path: str) -> None:
    """Write events to a JSONL file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    print(f"Wrote {len(events)} events to {output_path}")


def main():
    """Generate battery cell events and publish them to file/SQS.

    This is the CLI entry point used by the scripts in this package.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate sample battery cell events with module variance "
            "and publish to file/SQS."
        ),
    )
    parser.add_argument("--events", type=int, default=10, help="No of sample events")
    default_output = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "sample_events_mvp.jsonl"
    )
    parser.add_argument(
        "--output", type=str, default=default_output, help="Output file path"
    )
    parser.add_argument(
        "--mode",
        choices=["file", "sqs", "both"],
        default="file",
        help="Output mode: file, sqs, or both",
    )
    args = parser.parse_args()

    events = generate_events(args.events)

    if args.mode in ("file", "both"):
        write_events_to_file(events, args.output)

    if args.mode in ("sqs", "both"):
        queue_url = os.getenv("SQS_QUEUE_URL")
        if not queue_url:
            raise ValueError("SQS_QUEUE_URL not found in environment")
        publish_to_sqs(events, queue_url)


if __name__ == "__main__":
    main()
