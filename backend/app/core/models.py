from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlaneBase(BaseModel):
    id: str
    lat: float
    lon: float
    alt: int = 0
    heading: float = 0
    callsign: Optional[str] = ""
    squawk: Optional[str] = ""
    speed: float = 0


class PlaneResponse(PlaneBase):
    timestamp: str


class ShipBase(BaseModel):
    id: str
    lat: float
    lon: float
    heading: float = 0
    speed: float = 0
    name: str = ""
    destination: str = ""
    ship_type: str = ""


class ShipResponse(ShipBase):
    timestamp: str


class EventBase(BaseModel):
    id: str
    lat: float
    lon: float
    event_text: str
    tone: float = 0
    category: str = ""
    source_url: str = ""


class EventResponse(EventBase):
    date: str


class MetadataResponse(BaseModel):
    status: str
    phase: int
    planes_count: int = 0
    ships_count: int = 0
    last_planes_update: Optional[str] = None
    last_ships_update: Optional[str] = None


class WSMessage(BaseModel):
    type: str  # "plane", "ship", "event", "heartbeat"
    data: dict
