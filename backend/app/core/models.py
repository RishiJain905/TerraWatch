from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Plane(BaseModel):
    id: str
    lat: float
    lon: float
    alt: int = 0
    heading: float = 0
    callsign: str = ""
    squawk: str = ""
    speed: float = 0
    timestamp: Optional[str] = None


class Ship(BaseModel):
    id: str
    lat: float
    lon: float
    heading: float = 0
    speed: float = 0
    name: str = ""
    destination: str = ""
    ship_type: str = ""
    timestamp: Optional[str] = None


class PlaneRouteAirport(BaseModel):
    name: str = ""
    iata: str = ""
    icao: str = ""
    lat: float | None = None
    lon: float | None = None


class PlaneRoute(BaseModel):
    plane_id: str
    resolved_by: Literal["icao24", "callsign", "none"] = "none"
    status: Literal["ok", "not_found", "rate_limited", "error"] = "not_found"
    provider: str = "aviationstack"
    flight_iata: str = ""
    flight_icao: str = ""
    airline_name: str = ""
    airline_iata: str = ""
    airline_icao: str = ""
    departure: PlaneRouteAirport = Field(default_factory=PlaneRouteAirport)
    arrival: PlaneRouteAirport = Field(default_factory=PlaneRouteAirport)
    last_updated: Optional[str] = None


class WorldEvent(BaseModel):
    id: str
    date: str
    lat: float
    lon: float
    event_text: str
    tone: float = 0
    category: str = ""
    source_url: str = ""



class Metadata(BaseModel):
    status: str
    phase: int = 1
    planes_count: int = 0
    ships_count: int = 0
    events_count: int = 0
    last_planes_update: Optional[str] = None
    last_ships_update: Optional[str] = None
    last_events_update: Optional[str] = None


class WSMessage(BaseModel):
    type: Literal["plane", "ship", "event", "heartbeat", "metadata"]
    data: dict
    timestamp: str = Field(default_factory=utc_now_iso)
