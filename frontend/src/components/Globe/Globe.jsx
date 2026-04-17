import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { IconLayer, BitmapLayer, ScatterplotLayer } from '@deck.gl/layers'
import { getPlaneIcon } from '../../utils/planeIcons'
import { getShipIcon, SHIP_TYPE_COLORS } from '../../utils/shipIcons'
import { buildTerminatorImage } from '../../utils/terminator'
import { getStarfieldDataUrl } from '../../utils/starfield'
import { useWebSocket } from '../../hooks/useWebSocket'
import { usePlanes } from '../../hooks/usePlanes'
import { useShips } from '../../hooks/useShips'
import { useEvents } from '../../hooks/useEvents'
import { useConflicts } from '../../hooks/useConflicts'
import './Globe.css'

// Terminator texture is recomputed once per minute; the sun moves ~0.25°
// across the sky in that window, well below a single pixel at 720×360.
const TERMINATOR_REFRESH_MS = 60_000

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

// Ship type entries for the legend
const SHIP_LEGEND = [
  { type: 'cargo',     label: 'Cargo',     color: SHIP_TYPE_COLORS.cargo.hex },
  { type: 'tanker',    label: 'Tanker',    color: SHIP_TYPE_COLORS.tanker.hex },
  { type: 'passenger', label: 'Passenger', color: SHIP_TYPE_COLORS.passenger.hex },
  { type: 'fishing',   label: 'Fishing',   color: SHIP_TYPE_COLORS.fishing.hex },
  { type: 'other',     label: 'Other',     color: SHIP_TYPE_COLORS.other.hex },
]

function rowFromPick(info, dataArray) {
  if (!info) return null
  return info.object ?? (info.index >= 0 ? dataArray[info.index] : null)
}

export default function Globe({ layers, onEntityClick, onFilterHooksReady, onFiltersChange }) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const deckRef = useRef(null)

  // Starfield URL is generated exactly once per page load.
  const starfieldUrl = useMemo(() => getStarfieldDataUrl(), [])

  // Terminator raster: built from the current clock, rebuilt every minute.
  // deck.gl v9's BitmapLayer accepts an HTMLCanvasElement but not raw
  // ImageData — so the util produces ImageData and we paint it into a
  // canvas once per tick. useMemo keeps the canvas stable between renders
  // so deck.gl doesn't re-upload unchanged pixels on every react pass.
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), TERMINATOR_REFRESH_MS)
    return () => clearInterval(id)
  }, [])
  const terminatorImage = useMemo(() => {
    const imgData = buildTerminatorImage(now)
    const canvas = document.createElement('canvas')
    canvas.width = imgData.width
    canvas.height = imgData.height
    const ctx = canvas.getContext('2d')
    ctx.putImageData(imgData, 0, 0)
    return canvas
  }, [now])

  // Atmosphere overlay geometry — center + on-screen globe radius, computed
  // from the live deck.gl viewport so the rim glow tracks pan/zoom rather
  // than sitting at a fixed viewport-relative oval.
  const [atmosphere, setAtmosphere] = useState({ cx: 0, cy: 0, r: 0, ready: false })
  const updateAtmosphere = useCallback(() => {
    const deck = deckRef.current?.deck
    // deck.isInitialized is a public getter that returns `viewManager !== null`.
    // getViewports() unconditionally asserts viewManager is non-null and throws
    // synchronously before init finishes, which would crash the whole Globe
    // subtree on first render. Guard and wrap defensively.
    if (!deck || !deck.isInitialized) return
    try {
      const vp = deck.getViewports?.()[0]
      if (!vp || !vp.width || !vp.height) return
      // deck.gl's GlobeView is a perspective projection, so the visible limb
      // lives at a geodesic angle `d_limb = acos(R / C)` from the sub-observer
      // — NOT at a fixed 90°. As the camera distance C approaches R (zooming
      // in), d_limb shrinks and any 90° sample point sits behind the visible
      // limb, projecting INSIDE the actual on-screen circumference. That's
      // why a naive 90° probe pulls the rim inward at high zoom and collapses
      // it near the poles.
      //
      // Screen radius as a function of geodesic d:
      //   r(d) = f · R · sin(d) / (C − R·cos(d))
      // which is unimodal with argmax at d_limb. Sampling a grid of geodesic
      // distances (8 bearings × 15 radii) and taking the maximum projected
      // screen distance robustly recovers the on-screen globe radius at any
      // zoom, latitude, or bearing — no assumptions about the projection
      // internals beyond "visible limb = max projected radius".
      const center = vp.project([viewState.longitude, viewState.latitude])
      const cx0 = Number.isFinite(center[0]) ? center[0] : vp.width / 2
      const cy0 = Number.isFinite(center[1]) ? center[1] : vp.height / 2
      const lat0 = (viewState.latitude * Math.PI) / 180
      const sinLat0 = Math.sin(lat0)
      const cosLat0 = Math.cos(lat0)
      const BEARINGS = 8
      const RADII = 15
      let rMax = 0
      for (let j = 1; j <= RADII; j++) {
        const dRad = (Math.PI / 2) * (j / RADII) // 6°, 12°, … 90°
        const sinD = Math.sin(dRad)
        const cosD = Math.cos(dRad)
        for (let i = 0; i < BEARINGS; i++) {
          const theta = (i * 2 * Math.PI) / BEARINGS
          const sinLat2 = sinLat0 * cosD + cosLat0 * sinD * Math.cos(theta)
          const sinLat2Clamped = sinLat2 > 1 ? 1 : sinLat2 < -1 ? -1 : sinLat2
          const lat2 = Math.asin(sinLat2Clamped)
          const dLonRad = Math.atan2(
            Math.sin(theta) * sinD * cosLat0,
            cosD - sinLat0 * sinLat2Clamped,
          )
          const lon2 =
            ((viewState.longitude + (dLonRad * 180) / Math.PI + 540) % 360) -
            180
          const lat2Deg = (lat2 * 180) / Math.PI
          const p = vp.project([lon2, lat2Deg])
          if (!Number.isFinite(p[0]) || !Number.isFinite(p[1])) continue
          const d = Math.hypot(p[0] - cx0, p[1] - cy0)
          if (d > rMax) rMax = d
        }
      }
      if (rMax <= 0) return
      setAtmosphere({ cx: cx0, cy: cy0, r: rMax, ready: true })
    } catch (_) {
      // Projection/viewport access can throw during init or transitions; keep
      // the previous overlay geometry rather than flashing the glow off.
    }
  }, [viewState.longitude, viewState.latitude])

  useEffect(() => {
    updateAtmosphere()
  }, [updateAtmosphere, viewState.zoom])

  useEffect(() => {
    window.addEventListener('resize', updateAtmosphere)
    return () => window.removeEventListener('resize', updateAtmosphere)
  }, [updateAtmosphere])
  const { events, filteredEvents, addEvents, filters: eventsFilters, updateFilter: eventsUpdateFilter } = useEvents()
  const { conflicts, filteredConflicts, addConflicts, filters: conflictsFilters, updateFilter: conflictsUpdateFilter } = useConflicts()
  const { planes, filteredPlanes, addPlane, addPlanes, removePlane, filters: planesFilters, updateFilter: planesUpdateFilter } = usePlanes()
  const { ships, filteredShips, addShip, addShips, removeShip, filters: shipsFilters, updateFilter: shipsUpdateFilter } = useShips()

  // Expose filter controls to parent via a ref-based stable interface.
  // The ref always holds the latest counts/filters without triggering re-renders
  // up the tree. We call onFilterHooksReady once on mount with a getter that
  // reads from the ref, so the parent receives a stable reference.
  const filterHooksRef = useRef(null)
  filterHooksRef.current = {
    planes: { filters: planesFilters, updateFilter: planesUpdateFilter, rawCount: planes.length, filteredCount: filteredPlanes.length },
    ships: { filters: shipsFilters, updateFilter: shipsUpdateFilter, rawCount: ships.length, filteredCount: filteredShips.length },
    events: { filters: eventsFilters, updateFilter: eventsUpdateFilter, rawCount: events.length, filteredCount: filteredEvents.length },
    conflicts: { filters: conflictsFilters, updateFilter: conflictsUpdateFilter, rawCount: conflicts.length, filteredCount: filteredConflicts.length },
  }

  useEffect(() => {
    if (onFilterHooksReady) {
      // Wrap getter in an outer function so React doesn't interpret it as a
      // state updater. Without the wrapper, React would call
      //   filterHooksGetter(prev) => filterHooksRef.current
      // returning the data object directly instead of storing the getter function.
      onFilterHooksReady(() => () => filterHooksRef.current)
    }
  }, [onFilterHooksReady])

  // Sidebar reads hooks via a getter on App re-render only; when filters change inside
  // Globe, bump App so controlled range inputs and checkboxes stay in sync.
  useEffect(() => {
    onFiltersChange?.()
  }, [planesFilters, shipsFilters, eventsFilters, conflictsFilters, onFiltersChange])

  // Handle WebSocket messages — planes + ships
  const handleWSMessage = useCallback((msg) => {
    if (msg.type === 'plane') {
      if (msg.action === 'remove' && msg.data?.id) {
        removePlane(msg.data.id)
        return
      }
      addPlane(msg.data)
    } else if (msg.type === 'plane_batch') {
      if (msg.data && Array.isArray(msg.data)) {
        addPlanes(msg.data)
      }
    } else if (msg.type === 'ship') {
      if (msg.action === 'remove' && msg.data?.id) {
        removeShip(msg.data.id)
        return
      }
      addShip(msg.data)
    } else if (msg.type === 'ship_batch') {
      if (msg.data && Array.isArray(msg.data)) {
        addShips(msg.data)
      }
    } else if (msg.type === 'event_batch') {
      if (msg.data && Array.isArray(msg.data)) { addEvents(msg.data) }
    } else if (msg.type === 'conflict_batch') {
      if (msg.data && Array.isArray(msg.data)) { addConflicts(msg.data) }
    }
  }, [addPlane, addPlanes, addShip, addShips, removePlane, removeShip, addEvents, addConflicts])

  const { connected } = useWebSocket(handleWSMessage)

  // Deck defaults pickingRadius to 0 (single pixel) — IconLayer misses unless cursor is exact.
  // When pointer-down picks nothing, re-query ships/planes with a pixel radius.
  const handleDeckClick = useCallback(
    (info) => {
      if (!onEntityClick || info.picked) return
      const api = deckRef.current
      if (!api?.pickMultipleObjects) return
      if (layers?.ships) {
        const hits = api.pickMultipleObjects({
          x: info.x,
          y: info.y,
          radius: 40,
          depth: 16,
          layerIds: ['ships-layer'],
        })
        const row = rowFromPick(hits[0], filteredShips)
        if (row) {
          onEntityClick('ship', row)
          return
        }
      }
      if (layers?.planes) {
        const hits = api.pickMultipleObjects({
          x: info.x,
          y: info.y,
          radius: 40,
          depth: 16,
          layerIds: ['planes-layer'],
        })
        const row = rowFromPick(hits[0], filteredPlanes)
        if (row) onEntityClick('plane', row)
      }
    },
    [onEntityClick, layers, filteredShips, filteredPlanes],
  )

  // Tile layer for dark basemap rendered on the globe
  const tileLayer = new TileLayer({
    id: 'base-tiles',
    data: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    minZoom: 0,
    maxZoom: 10,
    tileSize: 256,
    pickable: false,
    renderSubLayers: (props) => {
      const { boundingBox } = props.tile
      return new BitmapLayer(props, {
        data: undefined,
        image: props.data,
        bounds: [boundingBox[0][0], boundingBox[0][1], boundingBox[1][0], boundingBox[1][1]],
      })
    },
  })

  // Terminator raster — dark-blue twilight tint keyed off solar elevation.
  // Placed ABOVE the basemap so the night side visibly dims land/ocean tiles;
  // transparent on the day side so the tiles render unchanged.
  const terminatorLayer = new BitmapLayer({
    id: 'terminator-layer',
    image: terminatorImage,
    // Clamp to the Web Mercator-friendly latitude range to match the basemap.
    bounds: [-180, -85.0511, 180, 85.0511],
    opacity: 1,
    pickable: false,
    parameters: { depthTest: false },
  })

  // Build deck.gl layers (draw order: first = bottom). Ships/planes must be LAST so they
  // render on top and win picking — otherwise ScatterplotLayers steal clicks from vessels.
  const deckLayers = [tileLayer, terminatorLayer]

  // GDELT Events — under vessels for picking priority
  if (layers && layers.events) {
    deckLayers.push(
      new ScatterplotLayer({
        id: 'events-layer',
        data: filteredEvents,
        pickable: true,
        getPosition: d => [d.lon, d.lat],
        getFillColor: d => {
          const t = Math.max(-10, Math.min(10, d.tone || 0))
          const r = Math.round(Math.max(0, Math.min(255, 128 - t * 25.5)))
          const g = Math.round(Math.max(0, Math.min(255, 128 + t * 25.5)))
          return [r, g, 0, 200]
        },
        // ~35 km — smaller than 150 km default so dense GDELT points don’t blanket regions
        getRadius: 35000,
        radiusUnits: 'meters',
        onClick: (info) => {
          if (!onEntityClick) return false
          const api = deckRef.current
          if (layers?.ships && api?.pickMultipleObjects) {
            const sh = api.pickMultipleObjects({
              x: info.x,
              y: info.y,
              radius: 40,
              depth: 12,
              layerIds: ['ships-layer'],
            })
            const shipRow = rowFromPick(sh[0], filteredShips)
            if (shipRow) {
              onEntityClick('ship', shipRow)
              return true
            }
          }
          if (layers?.planes && api?.pickMultipleObjects) {
            const ph = api.pickMultipleObjects({
              x: info.x,
              y: info.y,
              radius: 40,
              depth: 12,
              layerIds: ['planes-layer'],
            })
            const planeRow = rowFromPick(ph[0], filteredPlanes)
            if (planeRow) {
              onEntityClick('plane', planeRow)
              return true
            }
          }
          const row = rowFromPick(info, filteredEvents)
          if (!row) return false
          onEntityClick('event', row)
          return true
        },
      })
    )
  }

  // Conflicts — HeatmapLayer does not draw on GlobeView; use scatter points (red) like events.
  if (layers && layers.conflicts) {
    deckLayers.push(
      new ScatterplotLayer({
        id: 'conflicts-layer',
        data: filteredConflicts,
        pickable: true,
        getPosition: d => [d.lon, d.lat],
        getFillColor: (d) => {
          const t = Math.max(-10, Math.min(10, d.tone || 0))
          const heat = Math.round(130 + Math.min(125, Math.abs(t) * 12))
          return [heat, 36, 36, 215]
        },
        // Slightly smaller than events so both layers stay readable when enabled together
        getRadius: 30000,
        radiusUnits: 'meters',
        onClick: (info) => {
          if (!onEntityClick) return false
          const api = deckRef.current
          if (layers?.ships && api?.pickMultipleObjects) {
            const sh = api.pickMultipleObjects({
              x: info.x,
              y: info.y,
              radius: 40,
              depth: 12,
              layerIds: ['ships-layer'],
            })
            const shipRow = rowFromPick(sh[0], filteredShips)
            if (shipRow) {
              onEntityClick('ship', shipRow)
              return true
            }
          }
          if (layers?.planes && api?.pickMultipleObjects) {
            const ph = api.pickMultipleObjects({
              x: info.x,
              y: info.y,
              radius: 40,
              depth: 12,
              layerIds: ['planes-layer'],
            })
            const planeRow = rowFromPick(ph[0], filteredPlanes)
            if (planeRow) {
              onEntityClick('plane', planeRow)
              return true
            }
          }
          const row = rowFromPick(info, filteredConflicts)
          if (!row) return false
          onEntityClick('conflict', row)
          return true
        },
      })
    )
  }

  // Plane layer — on top of heatmaps/scatter so clicks register on the icon
  if (layers && layers.planes) {
    deckLayers.push(
      new IconLayer({
        id: 'planes-layer',
        data: filteredPlanes,
        pickable: true,
        getIcon: d => getPlaneIcon(d.alt),
        getPosition: d => [d.lon, d.lat],
        getSize: 48,
        getAngle: d => -(d.heading || 0),
        pickingRadius: 28,
        onClick: (info) => {
          if (!onEntityClick) return false
          const row = rowFromPick(info, filteredPlanes)
          if (!row) return false
          onEntityClick('plane', row)
          return true
        },
        billboard: false,
      })
    )
  }

  // Ship layer — last so it wins over events/conflicts when layers overlap
  if (layers && layers.ships) {
    deckLayers.push(
      new IconLayer({
        id: 'ships-layer',
        data: filteredShips,
        pickable: true,
        getIcon: d => getShipIcon(d.ship_type),
        getPosition: d => [d.lon, d.lat],
        getSize: 48,
        getAngle: d => -(d.heading || 0),
        pickingRadius: 28,
        onClick: (info) => {
          if (!onEntityClick) return false
          const row = rowFromPick(info, filteredShips)
          if (!row) return false
          onEntityClick('ship', row)
          return true
        },
        billboard: false,
      })
    )
  }

  return (
    <div
      className="globe-container"
      style={{ '--starfield-bg': starfieldUrl }}
    >
      <DeckGL
        ref={deckRef}
        views={new GlobeView({ id: 'globe' })}
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs)}
        onLoad={updateAtmosphere}
        onResize={updateAtmosphere}
        controller={true}
        layers={deckLayers}
        pickingRadius={36}
        onClick={handleDeckClick}
      />
      {atmosphere.ready && (
        <svg
          className="atmosphere-overlay"
          aria-hidden="true"
          preserveAspectRatio="none"
        >
          <defs>
            <radialGradient
              id="atmosphere-haze"
              cx={atmosphere.cx}
              cy={atmosphere.cy}
              r={atmosphere.r * 1.55}
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="rgba(90, 140, 220, 0)" />
              <stop offset="58%" stopColor="rgba(90, 140, 220, 0)" />
              <stop offset="72%" stopColor="rgba(90, 140, 220, 0.10)" />
              <stop offset="100%" stopColor="rgba(30, 60, 120, 0)" />
            </radialGradient>
            <radialGradient
              id="atmosphere-rim"
              cx={atmosphere.cx}
              cy={atmosphere.cy}
              r={atmosphere.r * 1.12}
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="rgba(140, 180, 255, 0)" />
              <stop offset="88%" stopColor="rgba(140, 180, 255, 0)" />
              <stop
                offset={`${((atmosphere.r / (atmosphere.r * 1.12)) * 100).toFixed(2)}%`}
                stopColor="rgba(140, 180, 255, 0.22)"
              />
              <stop offset="100%" stopColor="rgba(140, 180, 255, 0)" />
            </radialGradient>
          </defs>
          <rect width="100%" height="100%" fill="url(#atmosphere-haze)" />
          <rect width="100%" height="100%" fill="url(#atmosphere-rim)" />
        </svg>
      )}
      <div className="globe-info">
        <span><span className="stat-label">Planes</span><span className="stat-value">{filteredPlanes.length === planes.length ? planes.length.toLocaleString() : `${filteredPlanes.length.toLocaleString()} / ${planes.length.toLocaleString()}`}</span></span>
        <span><span className="stat-label">Ships</span><span className="stat-value">{filteredShips.length === ships.length ? ships.length.toLocaleString() : `${filteredShips.length.toLocaleString()} / ${ships.length.toLocaleString()}`}</span></span>
        <span><span className="stat-label">Events</span><span className="stat-value">{filteredEvents.length === events.length ? events.length.toLocaleString() : `${filteredEvents.length.toLocaleString()} / ${events.length.toLocaleString()}`}</span></span>
        <span><span className="stat-label">Conflicts</span><span className="stat-value">{filteredConflicts.length === conflicts.length ? conflicts.length.toLocaleString() : `${filteredConflicts.length.toLocaleString()} / ${conflicts.length.toLocaleString()}`}</span></span>
        <span className={`ws-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? 'Live' : 'Reconnecting'}
        </span>
      </div>
      <div className="globe-legend">
        <div className="legend-section">
          <div className="legend-title">Aircraft Altitude</div>
          <div className="legend-item"><span className="legend-dot low"></span>Low (&lt;10k ft)</div>
          <div className="legend-item"><span className="legend-dot medium"></span>Medium (10-30k ft)</div>
          <div className="legend-item"><span className="legend-dot high"></span>High (&gt;30k ft)</div>
        </div>
        <div className="legend-divider"></div>
        <div className="legend-section">
          <div className="legend-title">Ship Types</div>
          {SHIP_LEGEND.map(entry => (
            <div className="legend-item" key={entry.type}>
              <span className="ship-icon" style={{ backgroundColor: entry.color }}></span>
              {entry.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
