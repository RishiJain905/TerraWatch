# Environment Variables

All configuration is driven by environment variables (or a `.env` file at the repo root).

## Data Source Configuration

| Variable | Default | Description |
|---|---|---|
| `ADSBLOL_BASE_URL` | `https://api.adsb.lol` | Base URL for the ADSB.lol API |
| `ADSBLOL_API_URL` | `""` | Full ADSB.lol API URL (overrides `ADSBLOL_BASE_URL` if set) |
| `ADSBLOL_LAT` | `37.6188056` | Latitude center for ADSB.lol radius queries |
| `ADSBLOL_LON` | `-122.3754167` | Longitude center for ADSB.lol radius queries |
| `ADSBLOL_RADIUS_NM` | `250` | Radius in nautical miles for ADSB.lol queries |
| `AISSTREAM_API_KEY` | `""` | API key for AISStream real-time ship tracking |
| `OPENSKY_CLIENT_ID` | `""` | OpenSky Network OAuth2 client ID |
| `OPENSKY_CLIENT_SECRET` | `""` | OpenSky Network OAuth2 client secret |

## Data Refresh Intervals

| Variable | Default | Description |
|---|---|---|
| `ADSB_REFRESH_SECONDS` | `120` | Seconds between ADSB plane data refreshes |
| `ADSBLOL_REFRESH_SECONDS` | `120` | Seconds between ADSB.lol plane data refreshes |
| `AIS_REFRESH_SECONDS` | `60` | Seconds between AIS ship data refreshes |
| `AISSTREAM_BATCH_INTERVAL_SECONDS` | `30` | Seconds between AISStream batch emissions |
| `GDELT_REFRESH_SECONDS` | `900` | Seconds between GDELT event data refreshes (15 min) |

## Stale Data Thresholds

These control how old data must be before it is considered stale and cleaned up from the database. Values are in **seconds**.

| Variable | Default | Description |
|---|---|---|
| `STALE_PLANE_SECONDS` | `300` | Seconds before plane data is considered stale (for DB cleanup) |
| `STALE_SHIP_SECONDS` | `600` | Seconds before ship data is considered stale (for DB cleanup) |
| `STALE_EVENT_SECONDS` | `3600` | Seconds before event data is considered stale (for DB cleanup) |
| `STALE_CONFLICT_SECONDS` | `3600` | Seconds before conflict data is considered stale (for DB cleanup) |

## General

| Variable | Default | Description |
|---|---|---|
| `PYTHON_ENV` | `development` | Runtime environment (`development` / `production`) |
