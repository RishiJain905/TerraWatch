"""
GDELT Service — fetches world events from the GDELT Project.

GDELT publishes hourly CSV export files. This service:
1. Fetches the latest export file list from the GDELT lastupdate endpoint
2. Downloads and stream-parses the CSV (pipe-delimited)
3. Normalizes each row to the WorldEvent contract
"""

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

GDELT_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# Column indices in the pipe-delimited GDELT CSV
_COL_GLOBAL_EVENT_ID = 0
_COL_SQL_DATE = 2
_COL_EVENT_CODE = 13
_COL_EVENT_ROOT_CODE = 15
_COL_AVG_TONE = 21
_COL_ACTOR1_GEO_LAT = 29
_COL_ACTOR1_GEO_LONG = 30
_COL_ACTION_GEO_LAT = 42
_COL_ACTION_GEO_LONG = 43
_COL_ACTION_GEO_FEATURE_ID = 44
_COL_DATE_ADDED = 57

# EventCode → category mapping
EVENT_CODE_CATEGORY_MAP: dict[str, str] = {
    "01": "diplomacy",
    "02": "material_help",
    "03": "train",
    "04": "yield",
    "05": "demonstrate",
    "08": "assault",
    "09": "fight",
    "10": "unconventional_mass_gvc",
    "12": "conventional_mass_gvc",
    "13": "force_range",
    "14": "protest",
    "17": "government_debate",
    "18": "rioting",
    "20": "disaster",
    "21": "health",
    "22": "weather",
}

# EventCode → human-readable description
EVENT_CODE_DESCRIPTION: dict[str, str] = {
    "01": "made a statement",
    "02": "appealed for material assistance",
    "03": "expressed intent to cooperate",
    "04": "yielded",
    "05": "demonstrated or rallied",
    "08": "assaulted",
    "09": "fought",
    "10": "used unconventional mass violence",
    "12": "used conventional mass violence",
    "13": "used force",
    "14": "protested",
    "17": "engaged in government debate",
    "18": "rioted",
    "20": "responded to disaster",
    "21": "addressed health issue",
    "22": "responded to weather event",
}


def _parse_date(date_str: str) -> str:
    """Parse GDELT date formats to ISO date string."""
    try:
        if len(date_str) == 14:
            # DATEADDED format: YYYYMMDDHHMMSS
            dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            return dt.strftime("%Y-%m-%d")
        elif len(date_str) == 8:
            # SQLDATE format: YYYYMMDD
            dt = datetime.strptime(date_str, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    return date_str


def _safe_float(value: str) -> float:
    """Parse a float from a string, returning 0.0 on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _parse_csv_line(line: str) -> list[str]:
    """Parse a pipe-delimited GDELT CSV line."""
    return line.strip().split("\t")


async def _get_latest_csv_url(client: httpx.AsyncClient) -> str | None:
    """Fetch the lastupdate.txt and extract the first (most recent) CSV URL."""
    try:
        response = await client.get(GDELT_LASTUPDATE_URL, timeout=30.0)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        if not lines:
            logger.warning("GDELT lastupdate.txt returned empty content")
            return None
        # Each line is: size<space>hash<space>url
        parts = lines[0].strip().split()
        if len(parts) >= 3:
            return parts[2]
        logger.warning("GDELT lastupdate.txt line has unexpected format: %s", lines[0])
        return None
    except Exception:
        logger.exception("Failed to fetch GDELT lastupdate.txt")
        return None


async def _download_and_parse_csv(client: httpx.AsyncClient, csv_url: str) -> list[dict]:
    """Download and stream-parse a GDELT CSV file."""
    events: list[dict] = []

    try:
        async with client.stream("GET", csv_url, timeout=60.0) as response:
            response.raise_for_status()

            async for line_bytes in response.aiter_lines():
                line = line_bytes.strip()
                if not line:
                    continue

                columns = _parse_csv_line(line)
                if len(columns) <= _COL_DATE_ADDED:
                    continue

                # Skip rows without geo coordinates
                action_lat = columns[_COL_ACTION_GEO_LAT].strip()
                action_lon = columns[_COL_ACTION_GEO_LONG].strip()
                if not action_lat or not action_lon:
                    continue

                try:
                    lat = float(action_lat)
                    lon = float(action_lon)
                except (ValueError, TypeError):
                    continue

                global_event_id = columns[_COL_GLOBAL_EVENT_ID].strip()
                event_code = columns[_COL_EVENT_CODE].strip()
                avg_tone = _safe_float(columns[_COL_AVG_TONE])
                date_added = columns[_COL_DATE_ADDED].strip()
                sql_date = columns[_COL_SQL_DATE].strip()

                # Determine category from event code
                root_code = columns[_COL_EVENT_ROOT_CODE].strip()
                category = EVENT_CODE_CATEGORY_MAP.get(root_code, "")

                # Build event text
                description = EVENT_CODE_DESCRIPTION.get(
                    root_code, f"Event code {root_code}"
                )
                event_text = description

                # Parse date
                date = _parse_date(sql_date) if sql_date else _parse_date(date_added)

                event = {
                    "id": f"gdelt_{global_event_id}",
                    "date": date,
                    "lat": lat,
                    "lon": lon,
                    "event_text": event_text,
                    "tone": avg_tone,
                    "category": category,
                    "source_url": csv_url,
                }
                events.append(event)

    except Exception:
        logger.exception("Failed to download/parse GDELT CSV from %s", csv_url)

    return events


async def fetch_events() -> list[dict]:
    """Fetch recent world events from GDELT.

    Returns a list of dicts matching the WorldEvent contract.
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        csv_url = await _get_latest_csv_url(client)
        if csv_url is None:
            logger.warning("No GDELT CSV URL found; returning empty events list")
            return []

        logger.info("Fetching GDELT events from %s", csv_url)
        events = await _download_and_parse_csv(client, csv_url)
        logger.info("Parsed %d GDELT events", len(events))
        return events
