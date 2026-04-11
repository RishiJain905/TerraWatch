# Task 4 — Plane Detail Endpoint
**Agent:** GPT 5.4 (Backend)
**Dependencies:** Task 2 (adsb_service.py complete)

## Goal

Implement `GET /api/planes/{icao24}` to return details for a specific plane.

## Context

- Read `backend/app/api/routes/planes.py`
- Read `backend/app/core/models.py`
- Read `backend/app/core/database.py`

## Steps

### 1. Review Current planes.py

```bash
cat backend/app/api/routes/planes.py
```

### 2. Add Detail Endpoint

Add to `backend/app/api/routes/planes.py`:

```python
@router.get("/{icao24}", response_model=Plane | None)
async def get_plane(icao24: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get details for a specific plane by ICAO24 address."""
    async with db.execute(
        "SELECT * FROM planes WHERE icao24 = ?", (icao24.lower(),)
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
```

### 3. Also Add /api/planes/count

```python
@router.get("/count")
async def get_plane_count(db: aiosqlite.Connection = Depends(get_db)):
    """Get total count of active planes."""
    async with db.execute("SELECT COUNT(*) as count FROM planes") as cursor:
        row = await cursor.fetchone()
        return {"count": row["count"]}
```

### 4. Test

```bash
curl http://localhost:8000/api/planes/count
curl http://localhost:8000/api/planes/a1b2c3  # use a real icao24 from /api/planes
```

## Output

- Updated `backend/app/api/routes/planes.py` with detail + count endpoints
- Test results
