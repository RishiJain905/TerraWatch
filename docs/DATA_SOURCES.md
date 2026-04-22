# TerraWatch Data Sources

TerraWatch currently uses free or freemium public sources for live aircraft, ship, and event coverage. Route enrichment uses Aviationstack when a plane is selected.

## Aircraft

### OpenSky Network

- Primary aircraft feed
- Global ADS-B coverage
- Used for the main plane refresh loop
- Anonymous access is rate limited, but sufficient for TerraWatch refresh intervals

Endpoint:

```text
https://opensky-network.org/api/states/all
```

### ADSB.lol

- Secondary aircraft feed
- Public regional v2 point API
- Used to augment OpenSky coverage
- Configured through `ADSBLOL_BASE_URL`, `ADSBLOL_LAT`, `ADSBLOL_LON`, and `ADSBLOL_RADIUS_NM`

Endpoint:

```text
https://api.adsb.lol/v2/point/{lat}/{lon}/{radius}
```

### Aviationstack

- Selected-plane route enrichment only
- Not polled for the full fleet
- Backend caches route and airport lookups
- Returns a stable route status: `ok`, `not_found`, `rate_limited`, or `error`

Endpoints:

```text
https://api.aviationstack.com/v1/flights
https://api.aviationstack.com/v1/airports
```

## Ships

### Digitraffic

- Primary ship source for Nordic and Baltic waters
- Provides location and metadata endpoints
- Used as the main ship refresh source

Endpoints:

```text
https://meri.digitraffic.fi/api/ais/v1/locations
https://meri.digitraffic.fi/api/ais/v1/vessels
```

### AISStream.io

- Global AIS backup stream
- Used as the preferred secondary ship source
- Buffered and merged with the latest Digitraffic snapshot before persistence
- Requires `AISSTREAM_API_KEY`

Endpoint:

```text
wss://stream.aisstream.io/v0/stream
```

## Events

### GDELT

- Global event source for world events and conflict visualization
- Used for both the event layer and the conflict heatmap subset
- Violent categories are filtered into the conflicts layer in the backend

Endpoints:

```text
http://data.gdeltproject.org/gdeltv2/lastupdate.txt
http://api.gdeltproject.org/api/v2/doc/doc?query=topic&format=json
```

## Notes

- Aircraft and ship data are merged and cleaned in the backend before being broadcast to the frontend.
- Conflict data is derived from GDELT event categories; it is not a separate upstream feed.
- `docs/API.md` documents the runtime endpoints exposed by the backend.
