# Phase 3 — Task 6: GLM 5.1 — Ship Info Panel

## Context

Ships now appear on the globe with directional icons. Clicking a ship should show a slide-in info panel with ship details — parallel to the existing PlaneInfoPanel.

## Instructions

You are GLM 5.1 (frontend specialist). Read these files first:
- `docs/ARCHITECTURE.md`
- `docs/phases/phase3/PHASE3_OVERVIEW.md`
- `docs/phases/phase3/P3-task5-done.md`
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx` (reference implementation)
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.css` (reference styles)
- `frontend/src/components/Globe/Globe.jsx` (where ship click is handled)
- `frontend/src/App.jsx` (where plane panel is rendered)

## Your Task

### 1. Create `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx`

Create a slide-in panel component for ship details:

```jsx
// Fields to display:
// - Ship name (prominent)
// - MMSI (ID)
// - Position: lat, lon
// - Heading: degrees + compass direction
// - Speed: knots
// - Destination: port/location
// - Ship type: cargo/tanker/passenger/fishing/other
// - Last seen: relative timestamp
```

Style it to match PlaneInfoPanel (glassmorphism, same slide-in animation, same positioning).

### 2. Create `frontend/src/components/ShipInfoPanel/ShipInfoPanel.css`

Mirror PlaneInfoPanel styling:
- Glassmorphism: semi-transparent background with backdrop blur
- Slide in from right
- Close button (X)
- Consistent typography and spacing

### 3. Update `frontend/src/App.jsx`

Add ship panel rendering (parallel to plane panel):

```jsx
// Add state for selected ship
const [selectedShip, setSelectedShip] = useState(null)

// Handle ship clicks from globe
const handleEntityClick = useCallback((type, entity) => {
  setSelectedEntity({ type, entity })
  if (type === 'plane') setSelectedPlane(entity)
  if (type === 'ship') setSelectedShip(entity)
  console.log(`Selected ${type}:`, entity)
}, [])

// Render ship panel
{selectedShip && (
  <ShipInfoPanel
    ship={selectedShip}
    onClose={() => setSelectedShip(null)}
  />
)}
```

### 4. Update `Globe.jsx`

Ensure ship click handler is wired correctly:

```jsx
onClick: (info) => onEntityClick && onEntityClick('ship', info.object)
```

Verify this is already the case (it was in the Phase 2 implementation).

## Ship Info Panel Design

```
┌──────────────────────────────┐
│ ✕                           │
│  🚢  MSC OSCAR               │  ← Ship name + icon
│  MMSI: 235456789            │
│                              │
│  TYPE      Cargo             │
│  HEADING   180° (South)      │
│  SPEED     18.5 kts          │
│  DEST      Los Angeles        │
│                              │
│  POSITION  34.05°N 118.25°W │
│  LAST SEEN 12 seconds ago    │
└──────────────────────────────┘
```

## Key Constraints

- Panel should match PlaneInfoPanel styling
- Should handle missing/null fields gracefully (show "—" for unknown)
- Close button must work
- Clicking outside should NOT close (only X button or selecting another entity)
- Ship panel and plane panel should NOT show simultaneously (only one panel open)

## Output Files

- `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx` — create
- `frontend/src/components/ShipInfoPanel/ShipInfoPanel.css` — create
- `frontend/src/App.jsx` — update to render ship panel
- `frontend/src/components/Globe/Globe.jsx` — verify click handler

## Verification

- Click any ship on globe → panel slides in from right
- All ship fields display correctly
- Close button dismisses panel
- Opening plane panel while ship panel is open replaces it (only one at a time)
- No console errors
