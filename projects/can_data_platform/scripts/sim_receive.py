"""
Simulate receiving events via a FastAPI endpoint.

Run the server with:
    uvicorn sim_receive:app --reload
"""

import datetime
import logging

import fastapi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a",
    filename="projects/01_can_data_platform/data/sim_receive.log",
)

app = fastapi.FastAPI()


@app.post("/events")
async def receive_event(event: dict):
    """Receive and log a single event posted to /events.

    Args:
        event (dict): The event's payload.

    Returns:
        dict: Success message.
    """
    logging.info("Received event: %s time %s", event, datetime.datetime.now())
    return {"status": "success"}
