"""
GDELT Service — fetches world events from the GDELT Project.

GDELT publishes hourly CSV export files. This service:
1. Fetches the latest export file list from the GDELT lastupdate endpoint
2. Downloads and stream-parses the CSV (tab-delimited)
3. Normalizes each row to the WorldEvent contract
"""

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

GDELT_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

_COL_GLOBAL_EVENT_ID = 0
_COL_SQL_DATE = 2
_COL_EVENT_CODE = 26      # 3-digit CAMEO event code (e.g. "042")
_COL_EVENT_ROOT_CODE = 26  # Root = first 2 digits of event code (e.g. "04")
_COL_AVG_TONE = 34
_COL_ACTION_GEO_LAT = 40
_COL_ACTION_GEO_LONG = 41
_COL_ACTION_GEO_FEATURE_ID = 44
_COL_DATE_ADDED = 59

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
    if not date_str:
        return date_str
    try:
        if len(date_str) == 14:
            # DATEADDED format: YYYYMMDDHHMMSS
            dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            return dt.strftime("%Y-%m-%d")
        elif len(date_str) == 8:
            # SQLDATE format: YYYYMMDD
            dt = datetime.strptime(date_str, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        elif len(date_str) == 6:
            # GDELT 2.0 sometimes uses YYYYMM (e.g., "202504")
            dt = datetime.strptime(date_str, "%Y%m")
            return dt.strftime("%Y-%m")
    except (ValueError, TypeError, IndexError):
        pass
    return date_str


def _safe_float(value: str) -> float:
    """Parse a float from a string, returning 0.0 on failure."""
    try:
        return float(value)
    except (ValueError, TypeError, IndexError):
        return 0.0


def _parse_csv_line(line: str) -> list[str]:
    """Parse a tab-delimited GDELT CSV line."""
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
    """Download and stream-parse a GDELT CSV file.

    The GDELT export is served as a .zip containing a single CSV.
    We collect the full response bytes, unzip in memory, then parse.
    This avoids binary-decoding issues with aiter_lines() on compressed content.
    """
    events: list[dict] = []

    try:
        # Download full zip into memory (it's ~42KB, very small)
        response = await client.get(csv_url, timeout=60.0)
        response.raise_for_status()
        zip_bytes = response.read()

        import zipfile, io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".CSV")]
            if not csv_names:
                logger.warning("No .CSV file found inside GDELT zip %s", csv_url)
                return []
            csv_name = csv_names[0]
            with zf.open(csv_name) as f:
                csv_text = f.read().decode("utf-8", errors="replace")

        for line in csv_text.split("\n"):
            line = line.strip()
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
            except (ValueError, TypeError, IndexError):
                continue

            global_event_id = columns[_COL_GLOBAL_EVENT_ID].strip()
            event_code = columns[_COL_EVENT_CODE].strip()
            avg_tone = _safe_float(columns[_COL_AVG_TONE])
            date_added = columns[_COL_DATE_ADDED].strip()
            sql_date = columns[_COL_SQL_DATE].strip()

            # Determine category from event code
            root_code = columns[_COL_EVENT_ROOT_CODE].strip()
            # root_code is the full 3-digit code; derive 2-digit root for category
            category = EVENT_CODE_CATEGORY_MAP.get(root_code[:2], "")

            # Build event text
            description = EVENT_CODE_DESCRIPTION.get(
                root_code, f"Event code {root_code}"
            )
            event_text = description

            # Parse date — prefer SQLDATE if valid, fallback to DATEADDED
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
