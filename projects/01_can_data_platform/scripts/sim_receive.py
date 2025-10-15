import fastapi
import datetime
import logging
"""Simulate receiving events via a FastAPI endpoint. Run the server with: uvicorn sim_receive:app --reload"""

logging.basicConfig (
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode= 'a',
    filename= 'projects/01_can_data_platform/data/sim_receive.log'
)

app = fastapi.FastAPI()

@app.post("/events")
async def receive_event(event: dict):
    logging.info(f"Received event: {event} at time {datetime.datetime.now()}")
    return {"status": "success"}
