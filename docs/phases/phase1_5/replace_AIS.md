# Phase 1.5 — Replace AIS Friends with aisstream.io

## Why Replace

AIS Friends requires contributing AIS data (NMEA hardware/antenna) to access their API. aisstream.io provides global AIS coverage via WebSocket with only a free API key — no hardware needed.

---

## Summary of Changes

**Replace:**
- `ais_friends_service.py` (AIS Friends REST polling, Bearer token auth)
- All AIS Friends config/env vars

**With:**
- `aisstream_service.py` (aisstream.io WebSocket stream, API key auth)

The rest of the pipeline stays the same — deduplication, schedulers, WebSocket broadcast, tests.

---

## aisstream.io Overview

| Attribute | Details |
|-----------|---------|
| **Coverage** | Global — AIS stations covering most major shipping lanes |
| **Protocol** | WebSocket (not REST polling) |
| **Auth** | API key in connection message |
| **Free tier** | Yes — free API key, global stream, no credit card |
| **Registration** | https://aisstream.io/ — sign up with GitHub |

---

## How aisstream.io Works

### Connection Flow

1. Connect to `wss://stream.aisstream.io/v0/stream`
2. Send subscription message with API key and bounding box
3. Receive streaming JSON messages as ships broadcast AIS

### Subscription Message

```json
{
  "Apikey": "YOUR_API_KEY",
  "BoundingBoxes": [[-90, -180], [90, 180]],
  "FiltersShipMMSI": [],
  "FilterMessageTypes": ["PositionReport"]
}
```

- `BoundingBoxes`: `[[lat_min, lon_min], [lat_max, lon_max]]` — use `[[-90, -180], [90, 180]]` for global
- `FilterMessageTypes`: subscribe to `PositionReport` for ship positions
- `FiltersShipMMSI`: empty array = all ships

### Incoming Message Format

```json
{
  "MessageType": "PositionReport",
  "Timestamp": "2025-07-20T12:00:00Z",
  "MMSI": "265510570",
  "Latitude": 59.288612,
  "Longitude": 18.915412,
  "COG": 167.1,
  "SOG": 0.0,
  "TrueHeading": 194,
  "Status": 4,
  "IMO": 0,
  "Callsign": "",
  "Name": "VESSEL NAME",
  "ShipType": 0,
  "Destination": "",
  "ETA": "",
  "Draught": 0
}
```

Key fields:
- `MMSI` — unique ship identifier (use for deduplication)
- `Latitude`, `Longitude` — position
- `COG` — course over ground (degrees)
- `SOG` — speed over ground (knots)
- `TrueHeading` — heading in degrees
- `Name` — vessel name
- `ShipType` — numeric ship type code
- `Destination`, `ETA`, `Draught` — voyage info

---

## Implementation Guide

### 1. New Service: `aisstream_service.py`

Location: `backend/app/services/aisstream_service.py`

**Architecture pattern:**

aisstream is a persistent WebSocket stream, not a periodic REST poll. The service should:

1. Maintain a persistent WebSocket connection
2. Handle reconnection on disconnect
3. Buffer messages and emit batch updates periodically (e.g., every 30s)
4. Map incoming messages to the `Ship` model

**Class structure:**

```python
class AisstreamService:
    def __init__(self, api_key: str, bbox: list = [[-90, -180], [90, 180]]):
        self.api_key = api_key
        self.bbox = bbox
        self.websocket_url = "wss://stream.aisstream.io/v0/stream"
        self._connection: websockets.WebSocketClientProtocol | None = None
        self._ships: dict[str, Ship] = {}  # mmsi -> Ship, buffered until batch emit

    async def connect(self):
        """Establish WebSocket connection and send subscription."""

    async def listen(self, batch_interval: int = 30):
        """
        Main loop: listen for messages, buffer ships.
        Every batch_interval seconds, yield current batch and clear buffer.
        """

    async def _handle_message(self, msg: dict):
        """Parse a PositionReport message, add to buffer."""

    def _map_to_ship(self, msg: dict) -> Ship:
        """Map aisstream message to Ship model."""

    async def close(self):
        """Clean WebSocket shutdown."""
```

**Key design decisions:**

- Buffer ships in memory (`_ships` dict keyed by MMSI) between batch intervals
- Every `batch_interval` seconds, emit all buffered ships as a batch, then clear
- On reconnect, re-send subscription message
- On error/disconnect, wait and reconnect with exponential backoff

### 2. WebSocket Integration in Scheduler

In `schedulers.py`, instead of `fetch_ships()` called every 60s:

```
1. Start aisstream_service.connect() — runs once at startup
2. Run aisstream_service.listen(batch_interval=30) — continuous loop
3. On each batch emit: deduplicate with Digitraffic, broadcast via WebSocket
```

The scheduler should start the aisstream listener as a background task alongside Digitraffic.

### 3. Mapping ShipType Code

aisstream returns `ShipType` as a numeric code. Map to string for consistency:

| Code | Type |
|------|------|
| 0 | undefined |
| 1 | reserved_for_future_use |
| 2 | reserved_for_future_use |
| ... | ... |
| 70 | tanker |
| 80 | cargo |
| 90 | other |

Use the standard IMO ship type mapping. If a code is unmapped, default to `"other"`.

### 4. Error Handling

- **Connection refused / network error:** log error, wait 5s, reconnect
- **Invalid JSON:** skip message, continue
- **API key invalid:** log critical error, do not retry — require fresh key
- **WebSocket disconnect:** attempt reconnect up to 3 times with backoff, then restart service

### 5. Config Changes

**`backend/app/config.py`** — replace AIS Friends config:

```python
# Remove:
# AIS_FRIENDS_API_KEY: str
# AIS_FRIENDS_REFRESH_SECONDS: int

# Add:
AISSTREAM_API_KEY: str  # Required — no default
AISSTREAM_BATCH_INTERVAL_SECONDS: int = 30  # How often to emit ship batches
```

**`.env.example`** — update:

```
# aisstream.io — global ship tracking via WebSocket (free API key at https://aisstream.io/)
AISSTREAM_API_KEY=your_api_key_here
AISSTREAM_BATCH_INTERVAL_SECONDS=30
```

---

## Deduplication with Digitraffic

The aisstream service emits ships as batches. Before each WebSocket broadcast:

```
1. Get Digitraffic ships (REST poll, current behavior)
2. Get aisstream ships (from latest batch buffer)
3. Run deduplicate_ships(digitraffic_ships, aisstream_ships)
4. Broadcast merged set
```

Since Digitraffic and aisstream are both AIS sources, the same deduplication logic applies:
- Key by `mmsi`
- Prefer more recent `timestamp`
- On tie, prefer Digitraffic (richer vessel metadata)
- Merge attributes from the losing entry

---

## Testing

### `backend/tests/test_aisstream_service.py`

Create tests:

1. **`test_connect_sends_subscription`** — mock websocket, verify subscription message with API key is sent
2. **`test_handle_message_parses_position_report`** — verify message JSON maps to Ship object correctly
3. **`test_shiptype_mapping`** — verify numeric codes map to string types
4. **`test_batch_interval_emit`** — verify ships are buffered and emitted every batch_interval
5. **`test_reconnect_on_disconnect`** — verify reconnection logic on connection drop
6. **`test_invalid_json_skipped`** — verify malformed messages don't crash the listener

### Integration Test

Manual test: connect to aisstream with a test API key, verify ships appear on the globe.

---

## File Changes Summary

| Action | File |
|--------|------|
| **CREATE** | `backend/app/services/aisstream_service.py` |
| **UPDATE** | `backend/app/tasks/schedulers.py` — swap ais_friends fetch loop for aisstream listener |
| **UPDATE** | `backend/app/config.py` — replace AIS_FRIENDS_* vars with AISSTREAM_* |
| **UPDATE** | `.env.example` — replace AIS Friends vars with aisstream vars |
| **DELETE** | `backend/app/services/ais_friends_service.py` (if no other code uses it) |
| **CREATE** | `backend/tests/test_aisstream_service.py` |
| **UPDATE** | `docs/DATA_SOURCES.md` — replace AIS Friends entry with aisstream |
| **UPDATE** | `docs/phases/phase1_5/PHASE1_5_OVERVIEW.md` — update ship source section |

---

## Registration

To get an API key:
1. Go to https://aisstream.io/
2. Sign up with GitHub account
3. Generate WebSocket API key from dashboard
4. Paste into `AISSTREAM_API_KEY` env var
