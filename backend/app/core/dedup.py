from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from app.core.models import Plane, Ship
from pydantic import ValidationError

PLANE_SOURCE_PRIORITY = "open_sky"
PLANE_SECONDARY_SOURCE = "adsblol"
SHIP_SOURCE_PRIORITY = "digitraffic"
SHIP_SECONDARY_SOURCE = "ais_friends"
MAX_FUTURE_SKEW_SECONDS = 30
PLANE_TIMESTAMP_ALIASES = ("time_position",)
SHIP_TIMESTAMP_ALIASES = ("last_position",)
SHIP_PROTECTED_FIELDS = {"id", "lat", "lon", "heading", "speed", "timestamp"}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_plane(plane: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(plane)
    normalized["id"] = _normalize_text(normalized.get("id")).lower()
    canonical_timestamp = _get_timestamp_value(normalized, PLANE_TIMESTAMP_ALIASES)
    if _has_timestamp_value(canonical_timestamp):
        normalized["timestamp"] = canonical_timestamp
    return Plane.model_validate(normalized).model_dump()


def _normalize_ship(ship: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(ship)
    normalized["id"] = _normalize_text(normalized.get("id"))
    canonical_timestamp = _get_timestamp_value(normalized, SHIP_TIMESTAMP_ALIASES)
    if _has_timestamp_value(canonical_timestamp):
        normalized["timestamp"] = canonical_timestamp
    return Ship.model_validate(normalized).model_dump()


def _has_timestamp_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _get_timestamp_value(record: dict[str, Any], aliases: tuple[str, ...] = ()) -> Any:
    timestamp = record.get("timestamp")
    if _has_timestamp_value(timestamp) and _parse_timestamp(timestamp) is not None:
        return timestamp

    for alias in aliases:
        alias_value = record.get(alias)
        if _has_timestamp_value(alias_value) and _parse_timestamp(alias_value) is not None:
            return alias_value

    return timestamp if _has_timestamp_value(timestamp) else None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None

        try:
            parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError:
            try:
                value = float(cleaned)
            except (TypeError, ValueError):
                return None
        else:
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if abs(numeric_value) >= 1_000_000_000_000:
        numeric_value /= 1000

    try:
        return datetime.fromtimestamp(numeric_value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _get_timestamp(record: dict[str, Any], aliases: tuple[str, ...] = ()) -> datetime | None:
    return _parse_timestamp(_get_timestamp_value(record, aliases))


def _is_recent_timestamp(timestamp: datetime, max_age_seconds: int, now: datetime) -> bool:
    age_seconds = (now - timestamp).total_seconds()
    return -MAX_FUTURE_SKEW_SECONDS <= age_seconds <= max_age_seconds


def _plane_key(plane: dict[str, Any]) -> str:
    return _normalize_text(plane.get("id")).upper()


def _ship_key(ship: dict[str, Any]) -> str:
    return _normalize_text(ship.get("id"))


def _has_metadata_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _plane_source_rank(source_name: str) -> int:
    return 2 if source_name == PLANE_SOURCE_PRIORITY else 1


def _ship_source_rank(source_name: str) -> int:
    return 2 if source_name == SHIP_SOURCE_PRIORITY else 1


def _merge_sources(existing_sources: list[str], candidate_source: str) -> list[str]:
    merged_sources = list(existing_sources)
    if candidate_source not in merged_sources:
        merged_sources.append(candidate_source)
    return merged_sources


def _with_sources(record: dict[str, Any], sources: list[str]) -> dict[str, Any]:
    record_with_sources = dict(record)
    record_with_sources["sources"] = list(sources)
    return record_with_sources


def _choose_record(
    existing_record: dict[str, Any],
    existing_source: str,
    candidate_record: dict[str, Any],
    candidate_source: str,
    source_rank: Callable[[str], int],
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    existing_timestamp = _get_timestamp(existing_record)
    candidate_timestamp = _get_timestamp(candidate_record)

    if (
        existing_timestamp is not None
        and candidate_timestamp is not None
        and existing_timestamp != candidate_timestamp
    ):
        if candidate_timestamp > existing_timestamp:
            return candidate_record, candidate_source, existing_record
        return existing_record, existing_source, candidate_record

    if existing_timestamp is None and candidate_timestamp is not None:
        return candidate_record, candidate_source, existing_record
    if existing_timestamp is not None and candidate_timestamp is None:
        return existing_record, existing_source, candidate_record

    if source_rank(candidate_source) > source_rank(existing_source):
        return candidate_record, candidate_source, existing_record

    return existing_record, existing_source, candidate_record


def _resolve_plane_record(
    existing_plane: dict[str, Any],
    existing_source: str,
    candidate_plane: dict[str, Any],
    candidate_source: str,
) -> tuple[dict[str, Any], str]:
    winner, winner_source, _loser = _choose_record(
        existing_plane,
        existing_source,
        candidate_plane,
        candidate_source,
        _plane_source_rank,
    )
    return _normalize_plane(winner), winner_source


def _merge_ship_metadata(preferred_ship: dict[str, Any], other_ship: dict[str, Any]) -> dict[str, Any]:
    merged_ship = dict(preferred_ship)

    for field in ("name", "destination", "ship_type"):
        if not _has_metadata_value(merged_ship.get(field)) and _has_metadata_value(other_ship.get(field)):
            merged_ship[field] = other_ship.get(field)

    for key, value in other_ship.items():
        if key in SHIP_PROTECTED_FIELDS or key in {"name", "destination", "ship_type"}:
            continue
        if not _has_metadata_value(merged_ship.get(key)) and _has_metadata_value(value):
            merged_ship[key] = value

    return merged_ship


def _resolve_ship_record(
    existing_ship: dict[str, Any],
    existing_source: str,
    candidate_ship: dict[str, Any],
    candidate_source: str,
) -> tuple[dict[str, Any], str]:
    winner, winner_source, loser = _choose_record(
        existing_ship,
        existing_source,
        candidate_ship,
        candidate_source,
        _ship_source_rank,
    )
    return _normalize_ship(_merge_ship_metadata(winner, loser)), winner_source


def _filter_recent_records(
    records: list[dict[str, Any]],
    *,
    max_age_seconds: int,
    now: datetime,
    key_fn: Callable[[dict[str, Any]], str],
    normalize_fn: Callable[[dict[str, Any]], dict[str, Any]],
    timestamp_aliases: tuple[str, ...] = (),
    require_parseable_timestamp: bool = False,
) -> list[dict[str, Any]]:
    filtered_records: list[dict[str, Any]] = []

    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            if not key_fn(record):
                continue

            timestamp = _get_timestamp(record, timestamp_aliases)
            if require_parseable_timestamp and timestamp is None:
                continue
            if timestamp is not None and not _is_recent_timestamp(timestamp, max_age_seconds, now):
                continue

            filtered_records.append(normalize_fn(record))
        except (ValidationError, TypeError, ValueError):
            continue

    return filtered_records


def filter_stale_planes_open_sky(
    planes: list[dict[str, Any]], max_age_seconds: int = 300
) -> list[dict[str, Any]]:
    return _filter_recent_records(
        planes,
        max_age_seconds=max_age_seconds,
        now=datetime.now(timezone.utc),
        key_fn=_plane_key,
        normalize_fn=_normalize_plane,
        timestamp_aliases=PLANE_TIMESTAMP_ALIASES,
    )


def filter_stale_planes_adsblol(
    planes: list[dict[str, Any]], max_age_seconds: int = 300
) -> list[dict[str, Any]]:
    return _filter_recent_records(
        planes,
        max_age_seconds=max_age_seconds,
        now=datetime.now(timezone.utc),
        key_fn=_plane_key,
        normalize_fn=_normalize_plane,
        timestamp_aliases=PLANE_TIMESTAMP_ALIASES,
        require_parseable_timestamp=True,
    )


def filter_stale_ships_digitraffic(
    ships: list[dict[str, Any]], max_age_seconds: int = 600
) -> list[dict[str, Any]]:
    return _filter_recent_records(
        ships,
        max_age_seconds=max_age_seconds,
        now=datetime.now(timezone.utc),
        key_fn=_ship_key,
        normalize_fn=_normalize_ship,
        timestamp_aliases=SHIP_TIMESTAMP_ALIASES,
    )


def filter_stale_ships_ais_friends(
    ships: list[dict[str, Any]], max_age_seconds: int = 600
) -> list[dict[str, Any]]:
    return _filter_recent_records(
        ships,
        max_age_seconds=max_age_seconds,
        now=datetime.now(timezone.utc),
        key_fn=_ship_key,
        normalize_fn=_normalize_ship,
        timestamp_aliases=SHIP_TIMESTAMP_ALIASES,
    )


def deduplicate_planes(
    open_sky_planes: list[dict[str, Any]],
    adsblol_planes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    filtered_open_sky = filter_stale_planes_open_sky(open_sky_planes)
    filtered_adsblol = filter_stale_planes_adsblol(adsblol_planes)
    merged_planes: dict[str, tuple[dict[str, Any], str, list[str]]] = {}

    for source_name, planes in (
        (PLANE_SOURCE_PRIORITY, filtered_open_sky),
        (PLANE_SECONDARY_SOURCE, filtered_adsblol),
    ):
        for plane in planes:
            key = _plane_key(plane)
            if not key:
                continue

            existing_entry = merged_planes.get(key)
            if existing_entry is None:
                merged_planes[key] = (plane, source_name, [source_name])
                continue

            resolved_plane, resolved_source = _resolve_plane_record(
                existing_entry[0],
                existing_entry[1],
                plane,
                source_name,
            )
            merged_planes[key] = (
                resolved_plane,
                resolved_source,
                _merge_sources(existing_entry[2], source_name),
            )

    return [_with_sources(_normalize_plane(plane), sources) for plane, _source_name, sources in merged_planes.values()]


def deduplicate_ships(
    digitraffic_ships: list[dict[str, Any]],
    ais_friends_ships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    filtered_digitraffic = filter_stale_ships_digitraffic(digitraffic_ships)
    filtered_ais_friends = filter_stale_ships_ais_friends(ais_friends_ships)
    merged_ships: dict[str, tuple[dict[str, Any], str, list[str]]] = {}

    for source_name, ships in (
        (SHIP_SOURCE_PRIORITY, filtered_digitraffic),
        (SHIP_SECONDARY_SOURCE, filtered_ais_friends),
    ):
        for ship in ships:
            key = _ship_key(ship)
            if not key:
                continue

            existing_entry = merged_ships.get(key)
            if existing_entry is None:
                merged_ships[key] = (ship, source_name, [source_name])
                continue

            resolved_ship, resolved_source = _resolve_ship_record(
                existing_entry[0],
                existing_entry[1],
                ship,
                source_name,
            )
            merged_ships[key] = (
                resolved_ship,
                resolved_source,
                _merge_sources(existing_entry[2], source_name),
            )

    return [_with_sources(_normalize_ship(ship), sources) for ship, _source_name, sources in merged_ships.values()]


__all__ = [
    "filter_stale_planes_open_sky",
    "filter_stale_planes_adsblol",
    "filter_stale_ships_digitraffic",
    "filter_stale_ships_ais_friends",
    "deduplicate_planes",
    "deduplicate_ships",
]
