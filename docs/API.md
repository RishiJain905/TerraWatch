# TerraWatch API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

## Endpoints

### `GET /`
Root endpoint.

### `GET /health`
Health check endpoint.

### `GET /api/metadata`
Returns aggregate counts and last-update timestamps.

### `GET /api/planes`
Returns all active planes.

### `GET /api/planes/count`
Returns `{ "count": number }` for active planes.

### `GET /api/planes/{icao24}`
Returns one plane or `null`.

### `GET /api/planes/{icao24}/route`
Returns Aviationstack route enrichment for a selected plane.
The response is a `PlaneRoute` object with route metadata, nested departure/arrival airport objects, and a status field.

### `GET /api/ships`
Returns all active ships.

### `GET /api/ships/count`
Returns `{ "count": number }` for active ships.

### `GET /api/ships/{mmsi}`
Returns one ship or `null`.

### `GET /api/events`
Returns all stored GDELT events.

### `GET /api/events/count`
Returns `{ "count": number }` for stored events.

### `GET /api/events/{event_id}`
Returns one event or `null`.

### `GET /api/conflicts`
Returns violent GDELT events used by the conflict heatmap.

### `GET /api/conflicts/count`
Returns `{ "count": number }` for violent events.

### `GET /api/conflicts/{conflict_id}`
Returns one violent event or `null`.

### `GET /api/stale-thresholds`
Returns the configured cleanup thresholds in seconds.

## WebSocket

### `WS /ws`
Real-time data stream.

Connection URL: `ws://localhost:8000/ws`

#### Incoming message types

- `heartbeat`
- `plane`
- `plane_batch`
- `ship`
- `ship_batch`
- `event_batch`
- `conflict_batch`

#### Example heartbeat

```json
{
  "type": "heartbeat",
  "data": {
    "status": "connected"
  },
  "timestamp": "2026-04-10T12:00:00Z"
}
```

#### Example plane batch

```json
{
  "type": "plane_batch",
  "action": "upsert",
  "data": [
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
  ],
  "timestamp": "2026-04-10T12:00:00Z"
}
```

#### Example route response

```json
{
  "plane_id": "abc123",
  "resolved_by": "icao24",
  "status": "ok",
  "provider": "aviationstack",
  "flight_iata": "BA123",
  "flight_icao": "BAW123",
  "airline_name": "British Airways",
  "airline_iata": "BA",
  "airline_icao": "BAW",
  "departure": {
    "name": "Heathrow Airport",
    "iata": "LHR",
    "icao": "EGLL",
    "lat": 51.4706,
    "lon": -0.4619
  },
  "arrival": {
    "name": "John F. Kennedy International Airport",
    "iata": "JFK",
    "icao": "KJFK",
    "lat": 40.6413,
    "lon": -73.7781
  },
  "last_updated": "2026-04-10T12:00:00Z"
}
```

## Error Responses

The API uses standard HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request |
| 404 | Not found |
| 500 | Internal server error |

Error payloads follow the standard FastAPI format:

```json
{
  "detail": "Error message here"
}
```
