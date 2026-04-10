# TerraWatch — API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## Endpoints

### GET /
Root endpoint.

**Response:**
```json
{
  "name": "TerraWatch API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### GET /api/metadata
System metadata and counts.

**Response:**
```json
{
  "status": "ok",
  "phase": 1,
  "planes_count": 0,
  "ships_count": 0,
  "events_count": 0,
  "last_planes_update": null,
  "last_ships_update": null,
  "last_events_update": null
}
```

---

### GET /api/planes
Get all active planes.

**Response:**
```json
[
  {
    "id": "abc123",
    "lat": 51.5074,
    "lon": -0.1278,
    "alt": 35000,
    "heading": 270.5,
    "callsign": "BAW123",
    "squawk": "7000",
    "speed": 450.2,
    "timestamp": "2026-04-10T12:00:00Z"
  }
]
```

---

### GET /api/ships
Get all active ships.

**Response:**
```json
[
  {
    "id": "123456789",
    "lat": 1.3521,
    "lon": 103.8198,
    "heading": 180.0,
    "speed": 12.5,
    "name": "MV Example",
    "destination": "Singapore",
    "ship_type": "Cargo",
    "timestamp": "2026-04-10T12:00:00Z"
  }
]
```

---

### GET /api/events
Get world events.

**Response:**
```json
[
  {
    "id": "gdelt123",
    "date": "2026-04-10",
    "lat": 48.8566,
    "lon": 2.3522,
    "event_text": "Protest in Paris",
    "tone": -2.5,
    "category": "Protest",
    "source_url": "https://example.com"
  }
]
```

---

### WebSocket /ws

Real-time data stream. Connect via WebSocket protocol.

**Connection URL:** `ws://localhost:8000/ws`

**Incoming Messages:**

Heartbeat:
```json
{
  "type": "heartbeat",
  "data": {
    "status": "connected"
  },
  "timestamp": "2026-04-10T12:00:00Z"
}
```

Plane update:
```json
{
  "type": "plane",
  "data": {
    "id": "abc123",
    "lat": 51.5074,
    "lon": -0.1278,
    "alt": 35000,
    "heading": 270.5,
    "callsign": "BAW123",
    "speed": 450.2,
    "timestamp": "2026-04-10T12:00:00Z"
  }
}
```

Ship update:
```json
{
  "type": "ship",
  "data": {
    "id": "123456789",
    "lat": 1.3521,
    "lon": 103.8198,
    "heading": 180.0,
    "speed": 12.5,
    "name": "MV Example",
    "timestamp": "2026-04-10T12:00:00Z"
  }
}
```

---

## Error Responses

All endpoints return appropriate HTTP status codes:

| Code | Meaning |
|------|----------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

Error response format:
```json
{
  "detail": "Error message here"
}
```
