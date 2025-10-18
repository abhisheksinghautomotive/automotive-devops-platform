"""Module to send sample events to receiver endpoint and log results."""

import time
import json
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a',
    filename='projects/01_can_data_platform/data/sim_sender.log'
)


def send_events(events_path, endpoint="http://localhost:8000/events"):
    """Send events batch to endpoint, logging each event's status and timing.

    Args:
        events_path (str): Path to sample events JSONL file.
        endpoint (str): HTTP endpoint to POST each event to.
    """
    with open(events_path, "r", encoding="utf-8") as f:
        total_events = 0
        elapsed_times = []

        for line in f:
            event = json.loads(line)
            start_time = time.time()
            try:
                response = requests.post(endpoint, json=event, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                continue  # Skip to the next event

            elapsed_time = time.time() - start_time
            logging.info(
                "Sent event: %s, Response: %s, Time taken: %.4f seconds",
                event, response.status_code, elapsed_time
            )
            elapsed_times.append(elapsed_time)
            total_events += 1

        logging.info("Total Event Sent: %d", total_events)
        if total_events > 0:
            logging.info("Average latency: %.4f seconds",
                         sum(elapsed_times) / total_events)
            logging.info("Max latency: %.4f seconds", max(elapsed_times))
            logging.info("Min latency: %.4f seconds", min(elapsed_times))
        else:
            logging.info("No events were sent successfully.")


if __name__ == "__main__":
    send_events("projects/01_can_data_platform/data/sample_events_mvp.jsonl")
