# Phase 1.5 — Task 3: Deduplication Logic

**Agent:** GPT 5.4 (backend)
**Related overview:** `PHASE1_5_OVERVIEW.md`

---

## Objective

Create `dedup.py` with the deduplication and merging logic for both planes and ships. This module handles combining data from two sources (OpenSky + ADSB.lol for planes, Digitraffic + AIS Friends for ships) into a single unified set with smart merge and stale filtering.

---

## Background

Currently:
- Planes come from **one source** (OpenSky) → no deduplication needed
- Ships come from **one source** (Digitraffic) → no deduplication needed

After Phase 1.5:
- Planes come from **two sources** (OpenSky + ADSB.lol) → must deduplicate by `icao24`
- Ships come from **two sources** (Digitraffic + AIS Friends) → must deduplicate by `mmsi`

The dedup logic must be correct and tested — it's the core of this phase.

---

## Stale Entry Filtering

Before any deduplication, apply per-source stale filtering:

### Plane stale definition

| Source | Stale if |
|--------|----------|
| OpenSky | `time_position` older than 5 minutes |
| ADSB.lol | entry has no recent timestamp OR timestamp older than 5 minutes |

### Ship stale definition

| Source | Stale if |
|--------|----------|
| Digitraffic | position older than 10 minutes |
| AIS Friends | `timestamp` older than 10 minutes |

All stale entries are **dropped entirely** before merging.

---

## Plane Deduplication

### Input

```python
# Source A — OpenSky
open_sky_planes: List[Plane]

# Source B — ADSB.lol
adsblol_planes: List[Plane]
```

### Algorithm

```
1. Build a map: icao24_uppercase -> Plane (for open_sky_planes)
2. For each plane in adsblol_planes:
     key = icao24 normalized to uppercase
     if key not in merged_map:
         merged_map[key] = plane  # ADSB.lol entry
     else:
         # Duplicate icao24 found — resolve
         existing = merged_map[key]
         resolved = resolve_plane_conflict(existing, plane)
         merged_map[key] = resolved
3. Return list(merged_map.values())
```

### Conflict Resolution — Planes

Given two `Plane` objects for the same `icao24`:

1. **Prefer the entry with the more recent `time_position` or `timestamp`**
2. If both have the same timestamp or both are missing timestamps:
   - Prefer OpenSky (more established source, richer data model)

The resolved entry should carry **both** source tags so we can debug/audit:
```python
resolved.sources = ["open_sky", "adsblol"]  # or similar
```

### Edge Cases

- **Empty lists:** If one source returns empty, return the other source's planes
- **Complete overlap:** If both sources have identical icao24 sets, resolve by timestamp
- **Partial overlap:** Only conflicting icao24s are resolved, unique entries from both are kept

---

## Ship Deduplication

### Input

```python
# Source A — Digitraffic
digitraffic_ships: List[Ship]

# Source B — AIS Friends
ais_friends_ships: List[Ship]
```

### Algorithm

```
1. Build a map: mmsi -> Ship (for digitraffic_ships)
2. For each ship in ais_friends_ships:
     key = ship.mmsi
     if key not in merged_map:
         merged_map[key] = ship  # AIS Friends entry
     else:
         existing = merged_map[key]
         resolved = resolve_ship_conflict(existing, ship)
         merged_map[key] = resolved
3. Return list(merged_map.values())
```

### Conflict Resolution — Ships

Given two `Ship` objects for the same `mmsi`:

1. **Prefer the entry with the more recent `timestamp` or `last_position`**
2. If both have the same timestamp or both are missing:
   - Prefer Digitraffic (richer vessel metadata: names, destinations, type)
3. **Merge attributes:** For fields where the winner is missing but the loser has data, copy the attribute:
   - `name`, `destination`, `ship_type`, `length`, `width`, etc.
   - The winner's core fields (position, speed, heading) are preserved

The resolved entry should carry **both** source tags.

### Edge Cases

- **Empty lists:** If one source returns empty, return the other source's ships
- **Complete overlap:** Resolve by timestamp, prefer Digitraffic on tie
- **Partial overlap:** Same as planes — unique entries from both kept, conflicts resolved

---

## Implementation

### File: `backend/app/core/dedup.py`

Create a new module:

```python
from typing import List, Optional
from ..services.adsb_service import Plane
from ..services.ais_service import Ship

def filter_stale_planes_open_sky(planes: List[Plane], max_age_seconds: int = 300) -> List[Plane]:
    """Drop OpenSky planes with stale time_position."""
    ...

def filter_stale_planes_adsblol(planes: List[Plane], max_age_seconds: int = 300) -> List[Plane]:
    """Drop ADSB.lol planes with stale timestamp."""
    ...

def filter_stale_ships_digitraffic(ships: List[Ship], max_age_seconds: int = 600) -> List[Ship]:
    """Drop Digitraffic ships with stale timestamp."""
    ...

def filter_stale_ships_ais_friends(ships: List[Ship], max_age_seconds: int = 600) -> List[Ship]:
    """Drop AIS Friends ships with stale timestamp."""
    ...

def deduplicate_planes(open_sky_planes: List[Plane], adsblol_planes: List[Plane]) -> List[Plane]:
    """Merge two plane sources, deduplicating by icao24 (uppercase)."""
    ...

def deduplicate_ships(digitraffic_ships: List[Ship], ais_friends_ships: List[Ship]) -> List[Ship]:
    """Merge two ship sources, deduplicating by mmsi."""
    ...
```

### Internal helpers (private):

```python
def _resolve_plane_conflict(a: Plane, b: Plane) -> Plane:
    """Resolve conflicting Plane entries for the same icao24. Returns merged Plane."""
    ...

def _resolve_ship_conflict(a: Ship, b: Ship) -> Ship:
    """Resolve conflicting Ship entries for the same mmsi. Returns merged Ship."""
    ...

def _get_timestamp(plane_or_ship) -> Optional[datetime]:
    """Extract timestamp from a Plane or Ship object generically."""
    ...
```

---

## Testing

### `backend/tests/test_dedup.py`

Comprehensive unit tests:

#### Plane deduplication tests:

1. **`test_no_overlap`** — OpenSky has [A, B], ADSB.lol has [C, D]. Result: [A, B, C, D]. No conflicts.
2. **`test_full_overlap_same_timestamp`** — Both sources have [A, B] with same timestamp. Result: OpenSky wins (source priority).
3. **`test_full_overlap_diff_timestamp`** — A exists in both with timestamps T1 (OpenSky) and T2 (ADSB.lol), T2 is newer. Result: ADSB.lol entry wins.
4. **`test_partial_overlap`** — OpenSky has [A, B], ADSB.lol has [B, C]. Result: [A, B_from_adsblol_if_newer, C].
5. **`test_stale_open_sky_filtered`** — OpenSky returns [A, B] where B is stale. ADSB.lol returns [C]. Result: [A, C] (B dropped).
6. **`test_stale_adsblol_filtered`** — ADSB.lol returns [A] where A is stale. OpenSky returns [B]. Result: [B] (A dropped).
7. **`test_empty_source_a`** — OpenSky returns [], ADSB.lol returns [A, B]. Result: [A, B].
8. **`test_empty_source_b`** — OpenSky returns [A, B], ADSB.lol returns []. Result: [A, B].

#### Ship deduplication tests:

9. **`test_no_overlap_ships`** — Same pattern as planes.
10. **`test_full_overlap_ships_same_timestamp`** — Prefer Digitraffic on tie.
11. **`test_full_overlap_ships_diff_timestamp`** — Prefer newer.
12. **`test_partial_overlap_ships`** — Only conflicting mmsis are merged.
13. **`test_stale_ships_filtered`** — Stale entries from either source are dropped before merge.
14. **`test_attribute_merge`** — When Digitraffic wins but AIS Friends has `name` that Digitraffic is missing, the name is merged in.

---

## Completion Criteria

- `dedup.py` exists with all functions defined
- All 14 tests pass (7 plane + 7 ship cases)
- Stale filtering happens **before** deduplication in the actual scheduler code
- Conflict resolution correctly prioritizes newer timestamp, then source priority
- Attribute merge correctly copies non-conflicting fields from the losing entry
- No existing tests are broken
