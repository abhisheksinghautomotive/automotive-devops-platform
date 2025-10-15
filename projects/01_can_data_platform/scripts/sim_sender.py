import requests
import time
import json
import logging

logging.basicConfig (
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode= 'a',
    filename= 'projects/01_can_data_platform/data/sim_sender.log'
)

with open("projects/01_can_data_platform/data/sample_events_mvp.jsonl", "r") as f:
    total_events = 0
    elapsed_times = []
    for line in f:
        event = json.loads(line)
        start_time = time.time()
        try:
            response = requests.post("http://localhost:8000/events", json=event)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            continue  # Skip to the next event
        elapsed_time = time.time() - start_time
        logging.info(f"Sent event: {event}, Response: {response.status_code}, Time taken: {elapsed_time:.4f} seconds")
        elapsed_times.append(elapsed_time)
        total_events += 1

logging.info(f"Total Event Sent: {total_events}")
logging.info(f"Average latency: {sum(elapsed_times) / total_events:.4f} seconds")
logging.info(f"Max latency: {max(elapsed_times):.4f} seconds")
logging.info(f"Min latency: {min(elapsed_times):.4f} seconds")