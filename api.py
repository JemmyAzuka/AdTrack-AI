import os
from typing import Optional, Any
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from database import init_db, insert_event

app = FastAPI(title="AdTrack AI Event API", version="0.1.0")
init_db()

class ConversionEvent(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=200)
    source: str = Field(..., min_length=1, max_length=80)
    event_name: str = Field(default="Purchase", max_length=120)
    occurred_at: Optional[str] = None
    value: float = 0
    currency: str = "USD"
    order_id: Optional[str] = None
    email_hash: Optional[str] = None
    fbc: Optional[str] = None
    fbp: Optional[str] = None
    ttclid: Optional[str] = None
    gclid: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    properties: dict[str, Any] = {}

@app.get("/health")
def health():
    return {"status":"ok","service":"adtrack-ai"}

@app.post("/v1/events")
def receive_event(event: ConversionEvent, x_api_key: Optional[str] = Header(default=None)):
    expected = os.getenv("ADTRACK_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    accepted = insert_event(event.model_dump())
    return {"accepted":accepted,"duplicate":not accepted,"event_id":event.event_id}
