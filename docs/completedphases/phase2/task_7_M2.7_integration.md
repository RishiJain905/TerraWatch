# Task 7 — Integration Test: Live Aircraft on Globe
**Agent:** MiniMax M2.7 (Coordinator)
**Dependencies:** Tasks 3 (scheduler+WS), 5 (globe layer), 6 (info panel)

## Goal

Verify the full pipeline works end-to-end: ADSB Exchange → Backend → WebSocket → Frontend → Globe.

## Prerequisites

Tasks 3, 5, and 6 must be complete before starting this task.

## Steps

### 1. Verify All Tasks Complete

Confirm with the team:
- [ ] Task 3 done: scheduler running, /ws broadcasting, /api/planes returning data
- [ ] Task 5 done: IconLayer rendering planes on globe
- [ ] Task 6 done: click panel showing plane details

### 2. Start Backend

```bash
cd backend
pip install -r requirements.txt  # ensure httpx installed
python -m uvicorn app.main:app --reload --port 8000
```

In another terminal, check the scheduler is running:
```bash
curl http://localhost:8000/api/planes | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Planes in DB: {len(d)}')"
```

Should return planes (probably 0 at first, wait 30 seconds for first fetch).

### 3. Start Frontend

```bash
cd frontend
npm install  # if needed
npm run dev
```

### 4. Open Browser

Navigate to `http://localhost:5173`. Open browser DevTools.

### 5. Check WebSocket Connection

In DevTools console or Network tab:
- [ ] WebSocket to `ws://localhost:8000/ws` established
- [ ] Messages arriving with `type: "plane"` data

### 6. Verify Planes on Globe

- [ ] Globe renders
- [ ] Plane icons appear (wait up to 30 seconds for first fetch)
- [ ] Icons are directional (rotated by heading)
- [ ] Colors vary by altitude (green/yellow/red)
- [ ] Legend visible

### 7. Test Click Interaction

- [ ] Click a plane icon
- [ ] Info panel appears top-right
- [ ] Panel shows callsign, altitude, speed, heading, squawk, position
- [ ] Close button dismisses panel

### 8. Test Multiple Tabs

Open a second browser tab:
- [ ] Both tabs show same planes
- [ ] Updates in one tab appear in the other (via WS broadcast)

### 9. Test Data Freshness

Wait 30 seconds:
- [ ] Plane count updates automatically (new fetch cycle)
- [ ] Timestamps in WebSocket messages update

### 10. Capture Any Issues

Document any errors, bugs, or UX issues found.

### 11. Final Cleanup

If everything works:
1. Update `backend/app/tasks/schedulers.py` — remove debug print statements
2. Update README.md — remove "Next: Phase 2" and update Phase status
3. Create `docs/docs/completedphases/phase2/PHASE2_COMPLETE.md` summarizing what was built
4. Git commit all Phase 2 changes

## Success Criteria

All checks above must pass. If any fail, file issues and decide whether to fix in Phase 2 scope or defer.

## Output

- Integration test results (pass/fail for each check)
- List of any bugs found
- Updated README.md
- Phase 2 completion summary
- Git commit
