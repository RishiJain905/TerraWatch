# TerraWatch — Data Sources

All data sources are **free** and require **no paid API keys**.

---

## Aircraft Data

### ADSB Exchange

**What it is:** The world's largest cooperative network of aircraft trackers. Provides raw ADS-B (Automatic Dependent Surveillance-Broadcast) data — the same signals aircraft broadcast to air traffic control.

**Website:** https://www.adsbexchange.com/api/

**Free API:** No key required. Provides:
- Live aircraft positions (lat, lon, altitude, heading, speed)
- Callsigns and ICAO24 addresses
- Squawk codes
- Registration data

**Endpoint used:**
```
https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json
```

**Rate limits:** Reasonable use (one request per 30 seconds for V1 is fine)

**License:** Free for non-commercial use. Commercial use requires license — check their site.

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
| ADSB Exchange | Every 30 seconds | BackgroundTask scheduler |
| AIS/ORVRTS | Every 60 seconds | BackgroundTask scheduler |
| GDELT | Every hour | Scheduled job (downloading latest export) |
| ACLED | Once per day | Manual/scheduled CSV refresh |

---

## Legal Notes

- **ADSB Exchange:** Non-commercial use free. Check their ToS for commercial use restrictions.
- **AIS data:** Publicly broadcast data — free to use but some aggregators restrict commercial use.
- **GDELT:** Publicly compiled from news — free for analysis and research.
- **ACLED:** Free for academic and journalistic use with attribution. Check their data use policy.

Always respect the data source terms of service when using freely available data.
