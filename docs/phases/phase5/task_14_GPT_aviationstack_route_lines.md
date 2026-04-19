# Phase 5 — Task 14: Click-To-Reveal Flight Route Lines via Aviationstack

## Context

Read these files first:

- `backend/app/core/models.py`
- `backend/app/config.py`
- `backend/app/api/routes/planes.py`
- `backend/app/services/adsb_service.py`
- `backend/app/services/adsblol_service.py`
- `frontend/src/components/Globe/Globe.jsx`
- `frontend/src/components/Globe/Globe.css`
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`
- `docs/DATA_SOURCES.md`
- `docs/phases/phase5/task_4_GLM_flight_trails.md`
- `docs/phases/phase5/task_12_MiniMax_external_links_copy.md`

This task is intentionally **click-driven**. Do not enrich every plane in the fleet. The route lookup should happen only when a user selects a plane, with backend caching so repeated clicks on the same aircraft do not spam the upstream API.

## Product decision

Use **Aviationstack** as the route enrichment provider for selected planes.

Why this fits:

- It exposes live flight data with **departure** and **arrival** airport codes.
- It also exposes airport metadata with **latitude / longitude**.
- TerraWatch can keep its current OpenSky / ADSB.lol live position pipeline and add route enrichment only for the selected plane.

Constraints to respect:

- Aviationstack free tier is small and intended for personal use; design the feature so request volume stays minimal.
- Real route lines are **best-effort**, not guaranteed. Many aircraft will not resolve cleanly.
- If route data is unavailable, the UI must fail quietly and remain usable.

## UI / UX baseline (Gotham — read before implementing)

- **Clutter control:** Route lines are **selection-only**. Never render origin/destination overlays for the whole fleet.
- **Layer ordering:** Route lines should sit **above** basemap/terminator and below plane icon picking targets. Keep the aircraft icon visually dominant.
- **Visual language:** Use the existing air semantic color family (`--accent-air`) for the active route family. Differentiate origin-side vs destination-side with **line pattern / opacity**, not an unrelated hue explosion.
- **Legend discipline:** Do not add permanent HUD legend chrome for a selection-only feature unless the interaction proves unclear.
- **Panel integration:** Route metadata belongs in `PlaneInfoPanel` as additional rows and status text, not a second floating card.

## Goal

When a user clicks a plane:

1. TerraWatch fetches route metadata for that **single** plane from the backend.
2. The backend resolves departure and arrival airports from Aviationstack.
3. The frontend draws:
   - a dotted line from **departure airport -> plane**
   - a dotted line from **plane -> arrival airport**
4. The route overlay disappears when the plane is deselected.
5. If no route is found, the plane still behaves normally and the panel shows a clear fallback state.

## Data model

### New backend response model

Add a route-specific model instead of stuffing optional fields into the existing `Plane` contract.

Suggested response shape:

```python
class PlaneRouteAirport(BaseModel):
    name: str = ""
    iata: str = ""
    icao: str = ""
    lat: float | None = None
    lon: float | None = None


class PlaneRoute(BaseModel):
    plane_id: str
    resolved_by: str = ""          # "icao24", "callsign", "none"
    status: str = "not_found"      # "ok", "not_found", "rate_limited", "error"
    provider: str = "aviationstack"
    flight_iata: str = ""
    flight_icao: str = ""
    airline_name: str = ""
    airline_iata: str = ""
    airline_icao: str = ""
    departure: PlaneRouteAirport = Field(default_factory=PlaneRouteAirport)
    arrival: PlaneRouteAirport = Field(default_factory=PlaneRouteAirport)
    last_updated: str | None = None
```

Do **not** modify `/api/planes` or the WebSocket payload shape for this feature. Keep route enrichment as a separate request path.

### New frontend route state

Keep route state separate from live plane state.

Suggested state in `App.jsx`:

```javascript
const [selectedPlaneRoute, setSelectedPlaneRoute] = useState(null)
const [selectedPlaneRouteStatus, setSelectedPlaneRouteStatus] = useState('idle')
```

Pass this into `Globe` and `PlaneInfoPanel` rather than mutating the plane object.

## Provider strategy

### Aviationstack lookup sequence

Use a **best-effort resolver**, in this order:

1. Try to resolve by **ICAO24** if Aviationstack exposes it on the live result.
2. Fall back to **callsign** if present and non-empty.
3. If multiple results match, pick the most plausible active flight:
   - exact aircraft identifier match wins
   - then exact callsign match
   - then closest live position to the TerraWatch plane
   - then most recently updated result

### Airport coordinate resolution

If the live flight payload already contains departure/arrival airport coordinates, use them directly.

If it only provides IATA/ICAO airport codes:

1. resolve each airport through the Aviationstack airports endpoint
2. cache airport coordinate lookups aggressively because airport data is stable

### Caching rules

Use backend in-memory TTL caches:

- `route_cache[(plane_id, callsign)]` -> 5 to 10 minutes
- `airport_cache[(iata, icao)]` -> 24 hours

Caching is mandatory. Without it, click spam will burn quota immediately.

## Backend implementation

### Config

Add Aviationstack configuration to `backend/app/config.py`:

```python
AVIATIONSTACK_ACCESS_KEY: str = os.getenv("AVIATIONSTACK_ACCESS_KEY", "")
AVIATIONSTACK_BASE_URL: str = os.getenv("AVIATIONSTACK_BASE_URL", "http://api.aviationstack.com/v1")
AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS: int = int(os.getenv("AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS", "600"))
AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS: int = int(os.getenv("AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS", "86400"))
```

### Service

Create `backend/app/services/aviationstack_service.py`.

Responsibilities:

- fetch live flight matches from Aviationstack
- choose the best matching flight for a TerraWatch plane
- resolve departure/arrival airport coordinates
- normalize into `PlaneRoute`
- translate upstream failures into stable local statuses

Suggested service API:

```python
class AviationstackService:
    async def get_plane_route(self, *, plane_id: str, callsign: str, lat: float, lon: float) -> PlaneRoute:
        ...
```

Keep all provider-specific matching logic here, not in FastAPI routes.

### API route

Add a route endpoint in `backend/app/api/routes/planes.py`:

```python
@router.get("/{icao24}/route", response_model=PlaneRoute)
async def get_plane_route(icao24: str, db: aiosqlite.Connection = Depends(get_db)):
    ...
```

Flow:

1. normalize `icao24`
2. load the plane row from SQLite
3. if plane missing, return `404`
4. if `AVIATIONSTACK_ACCESS_KEY` is missing, return `status="error"` or `503`
5. call `AviationstackService.get_plane_route(...)`
6. return normalized route payload

Prefer returning a stable JSON payload with `status` over throwing raw provider errors into the frontend.

### Error handling

Map provider outcomes into local statuses:

- no matching flight -> `not_found`
- upstream 429 -> `rate_limited`
- upstream/network parse issues -> `error`
- complete match -> `ok`

Never let frontend code depend on provider-specific error strings.

## Frontend implementation

### Fetch-on-select behavior

In `App.jsx`:

1. when `selectedPlane` changes, trigger route fetch
2. cancel / ignore stale responses if user selects a different plane before the fetch returns
3. clear route state when deselecting the plane

Suggested request:

```javascript
fetch(`/api/planes/${selectedPlane.id}/route`)
```

Keep the request in `App.jsx` or a small hook such as `frontend/src/hooks/usePlaneRoute.js`. Do not bury it inside `PlaneInfoPanel`.

### Globe rendering

In `frontend/src/components/Globe/Globe.jsx`, accept a `selectedPlaneRoute` prop.

Render route overlays only when:

- `selectedPlane` exists
- `selectedPlaneRoute?.status === 'ok'`
- both airport coordinates exist

Recommended overlay approach:

- use the same screen-projected SVG overlay strategy as the current selection-only trail work, if that path is already the most reliable on `GlobeView`
- otherwise use a deck.gl line primitive only if verified to render correctly on the globe in this repo

Represent the two legs separately:

```javascript
[
  { kind: 'origin', from: [dep.lon, dep.lat], to: [plane.lon, plane.lat] },
  { kind: 'destination', from: [plane.lon, plane.lat], to: [arr.lon, arr.lat] },
]
```

Style direction by line treatment:

- origin-side: lower opacity dotted line
- destination-side: brighter dotted line

Do not add arrowheads unless they are visually clean on the globe.

### Plane info panel

In `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`, add route rows:

- Airline
- Flight IATA / ICAO
- Departure airport
- Arrival airport
- Route status

Examples:

- `Departure: JFK / KJFK`
- `Arrival: LHR / EGLL`
- `Route: Not available`
- `Route: Rate limited`

Keep fallbacks explicit and short.

## File plan

### Backend

- Modify: `backend/app/config.py`
- Modify: `backend/app/core/models.py`
- Modify: `backend/app/api/routes/planes.py`
- Create: `backend/app/services/aviationstack_service.py`
- Create: `backend/tests/test_aviationstack_service.py`
- Update or create: `backend/tests/test_plane_routes.py`

### Frontend

- Modify: `frontend/src/App.jsx`
- Optionally create: `frontend/src/hooks/usePlaneRoute.js`
- Modify: `frontend/src/components/Globe/Globe.jsx`
- Modify: `frontend/src/components/Globe/Globe.css`
- Modify: `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`
- Modify: `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.css` if new row styling is needed

### Docs / env

- Modify: `docs/DATA_SOURCES.md`
- Modify: `.env.example`
- Optionally create: `docs/ENVIRONMENT.md` if env docs are being centralized elsewhere

## Testing strategy

### Backend tests

1. service returns `ok` when live flight + airports resolve
2. service returns `not_found` when no flight matches
3. service returns `rate_limited` on upstream 429
4. service uses cache on repeated lookups
5. airport cache prevents repeated airport endpoint calls
6. matching prefers exact ICAO24 over callsign-only matches
7. ambiguous callsign resolution picks nearest live position

Mock external HTTP with `httpx`-level stubs; do not hit Aviationstack in tests.

### Frontend tests

If frontend tests are available, cover:

1. route fetch triggers on plane selection
2. stale request response does not overwrite a newer selection
3. route overlay renders only on `status === 'ok'`
4. route overlay clears on deselect
5. panel shows fallback rows on `not_found` / `rate_limited`

If the repo still lacks a full React test harness, document manual verification and keep the route line rendering logic factored into a small pure helper so it can be unit tested cheaply.

## Manual verification

- [ ] Selecting a plane triggers exactly one route request
- [ ] Clicking the same plane repeatedly reuses backend cache behavior
- [ ] Deselecting the plane removes both route lines
- [ ] Plane icon remains visually above route overlay
- [ ] Route panel rows show departure / arrival correctly when available
- [ ] Missing route data does not break selection or the info panel
- [ ] Upstream rate limit surfaces as a calm fallback state, not an uncaught error
- [ ] No route lookup happens for non-selected planes
- [ ] `npm run build` passes
- [ ] backend test suite for the new service passes

## Performance / quota guardrails

- No fleet-wide enrichment
- No background route polling
- No prefetch on hover
- No route fetch retry loop in the browser
- Cache aggressively on the backend
- One request per plane selection is the upper bound

## Open questions to resolve during implementation

1. Does Aviationstack resolve live flights reliably by ICAO24 for the aircraft TerraWatch sees, or will callsign be the dominant path?
2. Is the free/personal tier sufficient for your actual usage, or is this feature expected to move to a paid key quickly?
3. Do we want route status text in the panel immediately (`Loading route...`) or silently wait for data?
4. Should route overlays remain visible while the plane stays selected even if the live plane position updates, or should the line endpoints recompute on every plane refresh? The default should be **yes, recompute**.

## Notes

- This feature is additive and should not change any existing WebSocket or `/api/planes` behavior.
- Keep the implementation small: current plane feed stays authoritative for live position; Aviationstack only enriches selection-time route metadata.
- If Aviationstack proves too noisy or too weak on identifier matching, the backend adapter boundary should make it easy to swap providers later without rewriting the frontend route overlay behavior.
