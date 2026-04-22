# Environment Variables

TerraWatch reads configuration from environment variables and a repo-root `.env` file.

## Runtime

| Variable | Default | Description |
|---|---|---|
| `PYTHON_ENV` | `development` | Runtime environment flag |
| `TERRAWATCH_DB_PATH` | `terrawatch.db` in the repo root | Override the SQLite database path |

## Aircraft

| Variable | Default | Description |
|---|---|---|
| `ADSBLOL_API_URL` | `""` | Full ADSB.lol API URL override |
| `ADSBLOL_BASE_URL` | `https://api.adsb.lol` | Base URL for ADSB.lol point queries |
| `ADSBLOL_LAT` | `37.6188056` | Latitude center for ADSB.lol regional queries |
| `ADSBLOL_LON` | `-122.3754167` | Longitude center for ADSB.lol regional queries |
| `ADSBLOL_RADIUS_NM` | `250` | Query radius in nautical miles |
| `ADSBLOL_REFRESH_SECONDS` | `120` | ADSB.lol refresh interval |
| `ADSB_REFRESH_SECONDS` | `120` | OpenSky refresh interval |
| `OPENSKY_CLIENT_ID` | `""` | OpenSky OAuth2 client ID |
| `OPENSKY_CLIENT_SECRET` | `""` | OpenSky OAuth2 client secret |
| `AVIATIONSTACK_ACCESS_KEY` | `""` | Aviationstack route enrichment API key |
| `AVIATIONSTACK_BASE_URL` | `https://api.aviationstack.com/v1` | Aviationstack base URL |
| `AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS` | `600` | Cache TTL for plane route lookups |
| `AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS` | `86400` | Cache TTL for airport lookups |

## Ships

| Variable | Default | Description |
|---|---|---|
| `AISSTREAM_API_KEY` | `""` | AISStream API key |
| `AISSTREAM_BATCH_INTERVAL_SECONDS` | `30` | Batch interval for AISStream messages |
| `AIS_REFRESH_SECONDS` | `60` | Digitraffic ship refresh interval |

## Events

| Variable | Default | Description |
|---|---|---|
| `GDELT_REFRESH_SECONDS` | `900` | GDELT refresh interval |

## Stale Cleanup

These values drive backend cleanup and the `/api/stale-thresholds` endpoint.

| Variable | Default | Description |
|---|---|---|
| `STALE_PLANE_SECONDS` | `300` | Plane cleanup threshold |
| `STALE_SHIP_SECONDS` | `600` | Ship cleanup threshold |
| `STALE_EVENT_SECONDS` | `3600` | Event cleanup threshold |
| `STALE_CONFLICT_SECONDS` | `3600` | Conflict cleanup threshold |

## Frontend

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Base API URL used by the frontend |
| `VITE_WS_URL` | `ws://localhost:8000` | WebSocket URL used by the frontend |
| `VITE_PROXY_TARGET` | `http://backend:8000` | Docker Vite proxy target for `/api` |
| `VITE_WS_PROXY_TARGET` | `ws://backend:8000` | Docker Vite proxy target for `/ws` |

## Notes

- `VITE_API_URL` and `VITE_WS_URL` are the primary frontend runtime variables.
- The proxy target variables are only needed for Docker or other non-localhost dev setups.
- The backend loads `.env` from the repo root first, then falls back to the current working directory.
