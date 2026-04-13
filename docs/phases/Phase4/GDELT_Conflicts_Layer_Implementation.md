# GDELT Conflicts Layer Implementation — Option 2

## Goal

Filter GDELT's violent events into the Conflicts heatmap layer, replacing the empty/conflicting ACLED layer. Both layers remain functional:
- **Events** — All GDELT events (diplomacy, protests, statements, etc.) via ScatterplotLayer
- **Conflicts** — Only violent/aggressive GDELT events via HeatmapLayer

---

## Why Option 2

1. **Both layers become useful** — Events shows everything, Conflicts shows just violent/aggressive events as a heatmap
2. **GDELT already categorizes events** — codes for assault (08), fight (09), rioting (18), mass violence (10, 12), force (13)
3. **Better UX** — users see actual conflict hotspots instead of an empty/confusing Conflicts layer
4. **Still free** — no API changes required, just frontend filtering logic

---

## Implementation: Frontend Filter (Recommended)

Modify `frontend/src/hooks/useConflicts.js`. Instead of fetching from a separate endpoint, filter GDELT's violent events into the conflicts state.

### Violent Event Categories

```javascript
const VIOLENT_CATEGORIES = ['assault', 'fight', 'rioting', 'mass_gvc', 'force'];
```

Category mapping (from GDELT event codes):

| Code | Category |
|------|----------|
| 08 | assault |
| 09 | fight |
| 18 | rioting |
| 10 | mass_gvc |
| 12 | mass_gvc |
| 13 | force |

### Option A: Fetch from existing `/api/events` and filter client-side

```javascript
// In useConflicts.js
const VIOLENT_CATEGORIES = ['assault', 'fight', 'rioting', 'mass_gvc', 'force'];

const fetchConflicts = useCallback(async () => {
  try {
    setLoading(true);
    // Reuse the events endpoint — GDELT already has all the data
    const res = await fetch('/api/events');
    const data = await res.json();
    // Filter to violent events only for the heatmap
    const violentEvents = data.filter(e => VIOLENT_CATEGORIES.includes(e.category));
    setConflicts(violentEvents);
    setError(null);
  } catch (e) {
    setError(e.message);
  } finally {
    setLoading(false);
  }
}, []);
```

### Option B: Add `/api/conflicts` backend endpoint

If you prefer backend filtering, add this to `backend/app/api/routes/conflicts.py`:

```python
from fastapi import APIRouter
from app.services.gdelt_service import gdelt_service

router = APIRouter()

VIOLENT_CATEGORIES = ['assault', 'fight', 'rioting', 'mass_gvc', 'force']

@router.get("/api/conflicts")
async def get_conflicts():
    events = await gdelt_service.fetch_events()
    # Filter to violent events only
    violent_events = [e for e in events if e.category in VIOLENT_CATEGORIES]
    return violent_events
```

**Recommendation: Option A** — less backend work, same result.

---

## Files to Modify

### Frontend
| File | Change |
|------|--------|
| `frontend/src/hooks/useConflicts.js` | Filter violent GDELT events into conflicts state |

### Backend (only if Option B)
| File | Change |
|------|--------|
| `backend/app/api/routes/conflicts.py` | Add `/api/conflicts` endpoint with category filter |

### Docs
| File | Change |
|------|--------|
| `docs/DATA_SOURCES.md` | Remove ACLED reference, document GDELT as source for both layers |

---

## Globe.jsx Configuration Check

Verify `frontend/src/components/Globe/Globe.jsx` expects these fields on conflict objects:
- `lat` or `latitude` — location
- `lng` or `longitude` — location
- `weight` — intensity for heatmap (use `tone` or `fatalities` if available)

Heatmap layer config (verify):
```javascript
new HeatmapLayer({
  id: 'conflicts-heatmap',
  data: conflicts,
  getPosition: d => [d.lng, d.lat],
  getWeight: d => Math.abs(d.tone) || 1,
  radiusPixels: 60,
  intensity: 1,
  threshold: 0.03,
  colorRange: [[255, 0, 0, 100], [255, 255, 0, 200], [255, 0, 0, 255]],
})
```

---

## Testing Checklist

- [ ] Conflicts layer shows data (not empty)
- [ ] Events layer still shows all GDELT events (not filtered)
- [ ] Heatmap renders correctly with violent events
- [ ] No console errors on load
- [ ] WebSocket updates propagate to both layers independently

---

## What NOT to Do

- Do NOT remove or modify the Events layer — it must stay intact
- Do NOT try to integrate ACLED — not accessible without researcher account
- Do NOT change backend unless Option B is chosen
