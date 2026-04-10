# TerraWatch — Data Sources

All data sources are **free** and require **no paid API keys**.

---

## Aircraft Data

### ADSB Exchange

**What it is:** The world's largest cooperative network of aircraft trackers. Provides raw ADS-B (Automatic Dependent Surveillance-Broadcast) data.

**Note:** The VirtualRadar endpoint (public-api.adsbexchange.com) is **deprecated** — it now returns an AWS ALB identifier and requires api-auth UUID header. Use OpenSky Network instead (below).

**Website:** https://www.adsbexchange.com/

---

### OpenSky Network — PRIMARY API

**What it is:** Free ADS-B network providing global aircraft tracking. No API key required.

**Website:** https://opensky-network.org/

**Endpoint:**
```
https://opensky-network.org/api/states/all
```

**No API key required** (anonymous access, rate limited to once every 10 seconds)

**Response format:** JSON with `states` array and `time` epoch.

Each state vector (array of 17 elements):
```
Index 0:  icao24        (string, hex ICAO24 address, e.g. "a1b2c3")
Index 1:  callsign      (string, e.g. "BAW123   ")
Index 2:  origin_country(string, e.g. "United Kingdom")
Index 3:  time_position (int, unix epoch seconds or null)
Index 4:  last_contact  (int, unix epoch seconds)
Index 5:  longitude     (float, decimal degrees)
Index 6:  latitude      (float, decimal degrees)
Index 7:  baro_altitude (float, meters MSL or null)
Index 8:  on_ground     (boolean)
Index 9:  velocity      (float, m/s ground speed)
Index 10: true_track    (float, degrees, 0=North, 90=East)
Index 11: vertical_rate (float, m/s)
Index 12: sensors       (array of int or null)
Index 13: geo_altitude  (float, meters or null)
Index 14: squawk        (string, e.g. "7200" or null)
Index 15: spi           (boolean, special purpose indicator)
Index 16: position_source (int, 0=ADS-B, 1=ASTERIX, 2=MLAT)
```

Sample API response:
```json
{
  "time": 1775845981,
  "states": [
    ["e8027c", "LPE2452 ", "Chile", 1775845976, 1775845976, -69.9544, 14.5331, 10668.0, false, 246.18, 21.58, -1.95, null, 10926.0, null, false, 0]
  ]
}
```

**Unit conversions needed:**
- baro_altitude: meters → feet (multiply by 3.28084)
- velocity: m/s → knots (multiply by 1.94384)

**Rate limits:** Anonymous users: 1 request per 10 seconds. Authenticated: higher limits. For V1 (30s refresh), anonymous is fine.

**Verified:** Tested 2026-04-10, returns ~12000 aircraft globally.

**License:** Free for non-commercial use. Citation: Schäfer et al., IPSN 2014.

---

## Maritime Data

### ORVRTS (Open Vessel Registration and Tracking System)

**What it is:** Free AIS (Automatic Identification System) feed aggregator. AIS transponders are legally required on most large vessels and broadcast position data.

**Website:** https://www.orvrts.com/ or https://www.vesselfinder.com/

**Free tier:** Limited queries, but sufficient for demo/V1 purposes.

**Alternative — AISHub:**
```
http://www.aishub.net/api
```
Free API with registration required. Provides MMSI, position, heading, speed, destination.

**Alternative — MarineTraffic (free tier):**
```
https://www.marinetraffic.com/
```
Free tier has rate limits but gives position + vessel details.

**Data provided:**
- MMSI (Maritime Mobile Service Identity)
- Ship name
- Position (lat, lon)
- Heading and speed
- Destination port
- Ship type (cargo, tanker, passenger, etc.)

**Rate limits:** Check each provider. ORVRTS is most generous for free.

---

## World Events & News

### GDELT Project

**What it is:** The largest, most comprehensive, and highest-resolution open dataset of human society ever compiled. Monitors print, broadcast, and web news in every country and translates into English.

**Website:** https://www.gdeltproject.org/

**Free — no API key required.**

**Data accessed via:** Their hourly/daily CSV/JSON files and the GKG (Global Knowledge Graph) database.

**Main API endpoint:**
```
http://data.gdeltproject.org/gdeltv2/lastupdate.txt
```
This gives you the URL of the latest data file.

**Another useful endpoint:**
```
http://api.gdeltproject.org/api/v2/doc/doc?query=topic&format=json
```

**What it provides:**
- Geolocated world events (lat, lon coordinates)
- Event type (protest, war, diplomacy, etc.)
- Tone of reporting (positive/negative)
- Source URL
- Date and time

**Rate limits:** No strict rate limit but be respectful. Downloading the hourly export files is the most efficient approach.

---

## Conflict Data

### ACLED (Armed Conflict Location and Event Data Project)

**What it is:** The most comprehensive open-source dataset on political violence and protest worldwide. Covers all countries from 1997 to present.

**Website:** https://www.acleddna.com/

**Free access:** Requires free registration on their website.

**Download page:** https://www.acleddna.com/acleddatanew/access-all-data/

**What it provides:**
- Conflict event locations (lat, lon)
- Event type (battles, explosions, riots, protests, etc.)
- Fatality counts
- Date and time
- Country and region
- Actor information

**Format:** CSV download. No real-time API — download periodically.

---

## Satellite Imagery (Future Phases)

### Sentinel Hub (Sentinel-2 satellite)

**Website:** https://www.sentinel-hub.com/

**Free tier:** 10,000 server requests/month free. Excellent for global satellite imagery.

**Coverage:** Europe and global major cities via Sentinel-2 satellites.

**Alternative — NASA Worldview:**
```
https://worldview.earthdata.nasa.gov/
```
No API key needed for basic usage.

---

## Additional Free Sources (for V2+)

### OpenStreetMap
- Base map tiles (free via Mapbox free tier or OpenStreetMap tiles)
- Useful for region boundaries, place labels

### UN Data
- Country boundaries, population data, economic indicators

### WHO COVID/Health data
- Historical health events, disease outbreaks mapped globally

---

## Data Refresh Strategy

| Source | V1 Refresh Rate | Method |
|--------|----------------|--------|
| OpenSky Network | Every 30 seconds | asyncio scheduler |
| AIS/ORVRTS | Every 60 seconds | BackgroundTask scheduler |
| GDELT | Every hour | Scheduled job (downloading latest export) |
| ACLED | Once per day | Manual/scheduled CSV refresh |

---

## Legal Notes

- **OpenSky Network:** Free for non-commercial use. Citation: Schäfer et al., IPSN 2014.
- **ADSB Exchange:** Non-commercial use free. Check their ToS for commercial use restrictions.
- **AIS data:** Publicly broadcast data — free to use but some aggregators restrict commercial use.
- **GDELT:** Publicly compiled from news — free for analysis and research.
- **ACLED:** Free for academic and journalistic use with attribution. Check their data use policy.

Always respect the data source terms of service when using freely available data.
