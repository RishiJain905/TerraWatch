"""
ADSB Service — fetches live plane data from OpenSky Network.
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any, List

import httpx

from app.core.models import Plane, utc_now_iso

OPENSKY_STATES_API = "https://opensky-network.org/api/states/all"
HTTP_TIMEOUT_SECONDS = 30.0
METERS_TO_FEET = 3.28084
MPS_TO_KNOTS = 1.94384
_HTTP_HEADERS = {"User-Agent": "TerraWatch/0.1"}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default

    if not isfinite(numeric):
        return default

    return numeric


def _epoch_to_iso(epoch_seconds: int | float | None) -> str:
    numeric_epoch = _safe_float(epoch_seconds)
    if numeric_epoch is None:
        return utc_now_iso()

    try:
        return datetime.fromtimestamp(numeric_epoch, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return utc_now_iso()


def _state_timestamp(state: list[Any], response_time: int | float | None) -> str:
    last_contact = state[4] if len(state) > 4 else None
    if _safe_float(last_contact) is not None:
        return _epoch_to_iso(last_contact)
    if _safe_float(response_time) is not None:
        return _epoch_to_iso(response_time)
    return utc_now_iso()


def _normalize_state(state: list[Any], response_time: int | float | None) -> dict | None:
    if len(state) < 17:
        return None

    icao24 = (state[0] or "").strip().lower()
    lon = _safe_float(state[5])
    lat = _safe_float(state[6])

    if not icao24 or lat is None or lon is None:
        return None

    callsign = (state[1] or "").strip()
    altitude_meters = _safe_float(state[7])
    velocity_mps = _safe_float(state[9])
    heading = _safe_float(state[10], 0.0) or 0.0
    squawk = state[14] or ""

    plane = Plane(
        id=icao24,
        callsign=callsign,
        lat=lat,
        lon=lon,
        alt=round(altitude_meters * METERS_TO_FEET) if altitude_meters is not None else 0,
        heading=heading,
        speed=round(velocity_mps * MPS_TO_KNOTS, 3) if velocity_mps is not None else 0.0,
        squawk=str(squawk),
        timestamp=_state_timestamp(state, response_time),
    )
    return plane.model_dump()


async def fetch_planes() -> List[dict]:
    """Fetch live plane positions from OpenSky and normalize them to the Plane contract."""
    try:
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers=_HTTP_HEADERS,
        ) as client:
            response = await client.get(OPENSKY_STATES_API)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    if not isinstance(data, dict):
        return []

    response_time = data.get("time")
    states = data.get("states") or []
    planes: List[dict] = []

    for state in states:
        if not isinstance(state, list):
            continue

        plane = _normalize_state(state, response_time)
        if plane is not None:
            planes.append(plane)

    return planes


async def fetch_plane_details(icao24: str) -> dict | None:
    """Fetch details for a specific plane by ICAO24 identifier."""
    normalized_icao24 = icao24.strip().lower()
    if not normalized_icao24:
        return None

    planes = await fetch_planes()
    for plane in planes:
        if plane.get("id") == normalized_icao24:
            return plane

    return None
