"""Persistent aisstream.io ship listener that preserves the existing Ship payload contract."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from math import isfinite
from time import monotonic
from typing import Any, AsyncIterator, Awaitable, Callable

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus

from app.config import settings
from app.core.models import Ship, utc_now_iso

AISSTREAM_STREAM_URL = "wss://stream.aisstream.io/v0/stream"
DEFAULT_BOUNDING_BOX = [[[-90, -180], [90, 180]]]
DEFAULT_MESSAGE_TYPES = [
    "PositionReport",
    "StandardClassBPositionReport",
    "ShipStaticData",
    "StaticDataReport",
]
OPEN_TIMEOUT_SECONDS = 10
PING_INTERVAL_SECONDS = 20
PING_TIMEOUT_SECONDS = 20
RECONNECT_BASE_DELAY_SECONDS = 1
RECONNECT_MAX_DELAY_SECONDS = 30

logger = logging.getLogger(__name__)


class AisstreamAuthError(Exception):
    """Raised when aisstream rejects authentication and retries should stop."""


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


def _safe_int(value: Any, default: int | None = None) -> int | None:
    numeric = _safe_float(value)
    if numeric is None:
        return default
    return int(numeric)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _normalize_timestamp(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None

        try:
            return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).isoformat()
        except ValueError:
            numeric_value = _safe_float(cleaned)
            if numeric_value is None:
                return None
            value = numeric_value

    numeric_timestamp = _safe_float(value)
    if numeric_timestamp is None:
        return None

    if abs(numeric_timestamp) >= 1_000_000_000_000:
        numeric_timestamp /= 1000

    try:
        return datetime.fromtimestamp(numeric_timestamp, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _map_ship_type(value: Any) -> str:
    numeric_code = _safe_int(value)
    if numeric_code is not None:
        if 70 <= numeric_code < 80:
            return "cargo"
        if 80 <= numeric_code < 90:
            return "tanker"
        if 60 <= numeric_code < 70:
            return "passenger"
        if numeric_code == 30:
            return "fishing"
        return "other"

    lowered = _normalize_text(value).lower()
    if not lowered:
        return "other"
    if any(token in lowered for token in ("cargo", "container", "bulk", "freight")):
        return "cargo"
    if "tanker" in lowered:
        return "tanker"
    if any(token in lowered for token in ("passenger", "ferry", "cruise")):
        return "passenger"
    if any(token in lowered for token in ("fish", "trawler")):
        return "fishing"
    return "other"


class AisstreamService:
    """Maintain a persistent aisstream.io websocket and emit normalized ship batches."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        websocket_url: str = AISSTREAM_STREAM_URL,
        bounding_box: list[list[list[float]]] | None = None,
        message_types: list[str] | None = None,
        connect_func: Callable[..., Awaitable[Any]] | None = None,
        sleep_func: Callable[[float], Awaitable[Any]] | None = None,
        time_func: Callable[[], float] | None = None,
    ) -> None:
        resolved_api_key = settings.AISSTREAM_API_KEY if api_key is None else api_key
        self.api_key = _normalize_text(resolved_api_key)
        self.websocket_url = websocket_url
        self.bounding_box = bounding_box or [[corner[:] for corner in box] for box in DEFAULT_BOUNDING_BOX]
        self.message_types = list(message_types or DEFAULT_MESSAGE_TYPES)
        self._connect_func = connect_func or websockets.connect
        self._sleep = sleep_func or asyncio.sleep
        self._time = time_func or monotonic
        self._connection: Any | None = None
        self._ships: dict[str, dict] = {}
        self._stop_requested = False
        self._auth_failed = False

    def _subscription_payload(self) -> dict[str, Any]:
        return {
            "APIKey": self.api_key,
            "BoundingBoxes": self.bounding_box,
            "FiltersShipMMSI": [],
            "FilterMessageTypes": self.message_types,
        }

    async def connect(self) -> bool:
        if self._stop_requested:
            return False

        if not self.api_key:
            logger.warning("AISSTREAM_API_KEY missing; aisstream listener disabled")
            return False

        if self._connection is not None and not getattr(self._connection, "closed", False):
            return True

        try:
            self._connection = await self._connect_func(
                self.websocket_url,
                open_timeout=OPEN_TIMEOUT_SECONDS,
                ping_interval=PING_INTERVAL_SECONDS,
                ping_timeout=PING_TIMEOUT_SECONDS,
            )
            await self._connection.send(json.dumps(self._subscription_payload()))
            logger.info("Connected to aisstream websocket")
            return True
        except Exception as exc:
            if self._error_indicates_auth(exc):
                self._auth_failed = True
                logger.error("aisstream authentication failed; check AISSTREAM_API_KEY: %s", exc)
            else:
                logger.warning("Failed to connect to aisstream websocket: %s", exc)
            await self._drop_connection()
            return False

    async def listen(self, batch_interval: int = 30) -> AsyncIterator[list[dict]]:
        try:
            if batch_interval <= 0:
                batch_interval = 1

            if not self.api_key:
                logger.info("Skipping aisstream listen loop because AISSTREAM_API_KEY is not configured")
                return

            reconnect_delay = RECONNECT_BASE_DELAY_SECONDS

            while not self._stop_requested:
                connected = await self.connect()
                if not connected:
                    if self._stop_requested or self._auth_failed or not self.api_key:
                        return
                    await self._sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, RECONNECT_MAX_DELAY_SECONDS)
                    continue

                reconnect_delay = RECONNECT_BASE_DELAY_SECONDS
                batch_started_at = self._time()

                while not self._stop_requested and self._connection is not None:
                    elapsed = self._time() - batch_started_at
                    if elapsed >= batch_interval:
                        batch = list(self._ships.values())
                        self._ships.clear()
                        batch_started_at = self._time()
                        if batch:
                            yield batch
                        continue

                    timeout = max(batch_interval - elapsed, 0.1)

                    try:
                        raw_message = await asyncio.wait_for(self._connection.recv(), timeout=timeout)
                        await self._handle_message(raw_message)
                    except asyncio.TimeoutError:
                        batch = list(self._ships.values())
                        self._ships.clear()
                        batch_started_at = self._time()
                        if batch:
                            yield batch
                    except asyncio.CancelledError:
                        await self.close()
                        raise
                    except AisstreamAuthError:
                        await self.close()
                        return
                    except ConnectionClosed as exc:
                        if self._error_indicates_auth(exc):
                            self._auth_failed = True
                            logger.error("aisstream connection closed due to authentication failure: %s", exc)
                            await self.close()
                            return
                        logger.warning("aisstream connection closed; reconnecting: %s", exc)
                        await self._drop_connection()
                        break
                    except Exception:
                        logger.exception("aisstream listener crashed while receiving data")
                        await self._drop_connection()
                        break

                if self._stop_requested or self._auth_failed:
                    return

                await self._sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, RECONNECT_MAX_DELAY_SECONDS)
        finally:
            if self._stop_requested:
                await self._drop_connection()

    async def _handle_message(self, raw_message: str | bytes | dict[str, Any]) -> dict | None:
        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8", errors="ignore")

        if isinstance(raw_message, str):
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning("Skipping invalid aisstream JSON message")
                return None
        elif isinstance(raw_message, dict):
            message = raw_message
        else:
            return None

        if self._is_auth_error_message(message):
            self._auth_failed = True
            logger.error("aisstream rejected AISSTREAM_API_KEY: %s", message)
            raise AisstreamAuthError("aisstream authentication rejected")

        fields = self._extract_ship_fields(message)
        ship_id = _normalize_text(fields.get("id"))
        if not ship_id:
            return None

        previous_ship = self._ships.get(ship_id, {})
        merged_fields = dict(previous_ship)
        for key, value in fields.items():
            if _is_present(value):
                merged_fields[key] = value
        merged_fields["id"] = ship_id

        ship = self._map_to_ship(merged_fields)
        if ship is None:
            return None

        self._ships[ship_id] = ship
        return ship

    def _map_to_ship(self, fields: dict[str, Any]) -> dict | None:
        ship_id = _normalize_text(fields.get("id"))
        lat = _safe_float(fields.get("lat"))
        lon = _safe_float(fields.get("lon"))
        if not ship_id or lat is None or lon is None:
            return None

        ship = Ship(
            id=ship_id,
            lat=lat,
            lon=lon,
            heading=_safe_float(fields.get("heading"), 0.0) or 0.0,
            speed=_safe_float(fields.get("speed"), 0.0) or 0.0,
            name=_normalize_text(fields.get("name")),
            destination=_normalize_text(fields.get("destination")),
            ship_type=_map_ship_type(fields.get("ship_type")),
            timestamp=_normalize_timestamp(fields.get("timestamp")) or utc_now_iso(),
        )
        return ship.model_dump()

    async def _drop_connection(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is not None and not getattr(connection, "closed", False):
            try:
                await connection.close()
            except Exception:
                logger.debug("Ignoring aisstream close error", exc_info=True)

    async def close(self) -> None:
        self._stop_requested = True
        await self._drop_connection()

    def _extract_ship_fields(self, message: dict[str, Any]) -> dict[str, Any]:
        metadata = message.get("MetaData") if isinstance(message.get("MetaData"), dict) else {}
        message_type = _normalize_text(message.get("MessageType"))

        payload: dict[str, Any] = {}
        wrapped_message = message.get("Message")
        if isinstance(wrapped_message, dict):
            preferred_payload = wrapped_message.get(message_type)
            if isinstance(preferred_payload, dict):
                payload = preferred_payload
            else:
                for value in wrapped_message.values():
                    if isinstance(value, dict):
                        payload = value
                        break
        elif isinstance(message.get(message_type), dict):
            payload = message[message_type]
        else:
            payload = message

        return {
            "id": _normalize_text(
                payload.get("UserID")
                or payload.get("MMSI")
                or metadata.get("MMSI")
                or message.get("UserID")
                or message.get("MMSI")
            ),
            "lat": _safe_float(
                payload.get("Latitude"),
                _safe_float(
                    payload.get("Lat"),
                    _safe_float(metadata.get("latitude"), _safe_float(metadata.get("Latitude"))),
                ),
            ),
            "lon": _safe_float(
                payload.get("Longitude"),
                _safe_float(
                    payload.get("Lon"),
                    _safe_float(metadata.get("longitude"), _safe_float(metadata.get("Longitude"))),
                ),
            ),
            "heading": _safe_float(
                payload.get("TrueHeading"),
                _safe_float(payload.get("Cog"), _safe_float(payload.get("COG"))),
            ),
            "speed": _safe_float(payload.get("Sog"), _safe_float(payload.get("SOG"))),
            "name": _normalize_text(metadata.get("ShipName") or payload.get("Name") or message.get("Name")),
            "destination": _normalize_text(payload.get("Destination") or message.get("Destination")),
            "ship_type": payload.get("ShipType") or message.get("ShipType") or payload.get("Type"),
            "timestamp": (
                metadata.get("time_utc")
                or metadata.get("timestamp_utc")
                or payload.get("Timestamp")
                or message.get("Timestamp")
                or message.get("time_utc")
            ),
        }

    def _is_auth_error_message(self, message: dict[str, Any]) -> bool:
        lowered = json.dumps(message, sort_keys=True).lower()
        auth_tokens = (
            "api key",
            "apikey",
            "authentication",
            "unauthorized",
            "forbidden",
            "invalid key",
        )
        return any(token in lowered for token in auth_tokens) and any(
            token in lowered for token in ("error", "failed", "reject", "unauthorized", "forbidden")
        )

    def _error_indicates_auth(self, error: Exception) -> bool:
        if isinstance(error, InvalidStatus):
            response = getattr(error, "response", None)
            if getattr(response, "status_code", None) in {401, 403}:
                return True

        status_code = getattr(error, "status_code", None)
        if status_code in {401, 403}:
            return True

        close_frame = getattr(error, "rcvd", None) or getattr(error, "sent", None)
        if getattr(close_frame, "code", None) in {1008, 4001, 4401, 4403}:
            return True

        reason_parts = [str(error)]
        close_reason = _normalize_text(getattr(close_frame, "reason", None))
        if close_reason:
            reason_parts.append(close_reason)

        reason = " ".join(part for part in reason_parts if part).lower()
        return any(token in reason for token in ("401", "403", "api key", "unauthorized", "forbidden", "authentication"))
