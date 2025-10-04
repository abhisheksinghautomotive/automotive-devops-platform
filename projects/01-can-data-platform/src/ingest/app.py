from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from src.utils.config import API_KEY  # absolute import so 'utils' resolves under 'src'

app = FastAPI()

BUFFER = []

class TelemetryMessage(BaseModel):
    vehicle_id: str
    can_id: str
    payload: dict

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
async def ingest(message: TelemetryMessage, request: Request):
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    enriched = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        **message.model_dump()
    }
    BUFFER.append(enriched)
    return {"accepted": True, "buffer_size": len(BUFFER)}

@app.get("/stats")
def stats():
    return {"buffer_size": len(BUFFER)}
