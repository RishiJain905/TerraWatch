import { useState, useCallback, useEffect, useRef } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { IconLayer, BitmapLayer, ScatterplotLayer, SolidPolygonLayer } from '@deck.gl/layers'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import { getPlaneIcon } from '../../utils/planeIcons'
import { getShipIcon, SHIP_TYPE_COLORS } from '../../utils/shipIcons'
import { useWebSocket } from '../../hooks/useWebSocket'
import { usePlanes } from '../../hooks/usePlanes'
import { useShips } from '../../hooks/useShips'
import { useEvents } from '../../hooks/useEvents'
import { useConflicts } from '../../hooks/useConflicts'
import './Globe.css'
import { getTerminatorPolygon } from '../../utils/terminator'
import { generateStarfield } from '../../utils/starfield'

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

// Generate starfield once — stable across re-renders (seeded PRNG)
const STARFIELD_DATA = generateStarfield({ count: 800, radius: 20000000, seed: 42 })

// Ship type entries for the legend
const SHIP_LEGEND = [
  { type: 'cargo',     label: 'Cargo',     color: SHIP_TYPE_COLORS.cargo.hex },
  { type: 'tanker',    label: 'Tanker',    color: SHIP_TYPE_COLORS.tanker.hex },
  { type: 'passenger', label: 'Passenger', color: SHIP_TYPE_COLORS.passenger.hex },
  { type: 'fishing',   label: 'Fishing',   color: SHIP_TYPE_COLORS.fishing.hex },
  { type: 'other',     label: 'Other',     color: SHIP_TYPE_COLORS.other.hex },
]

export default function Globe({ layers, onEntityClick, onFilterHooksReady }) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
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

  // Terminator polygon — recalculated every 60 seconds (terminator moves ~15°/hour)
  const [terminatorPolygon, setTerminatorPolygon] = useState(() => getTerminatorPolygon())

  useEffect(() => {
    const interval = setInterval(() => {
      setTerminatorPolygon(getTerminatorPolygon())
    }, 60000) // every minute
    return () => clearInterval(interval)
  }, [])

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

  // Starfield layer — scatter points on a large-radius sphere behind the globe
  const starfieldLayer = new ScatterplotLayer({
    id: 'starfield-layer',
    data: STARFIELD_DATA,
    pickable: false,
    getPosition: d => d.position,
    getFillColor: d => d.color,
    getRadius: d => d.radius,
    radiusUnits: 'meters',
    opacity: 0.9,
    stroked: false,
  })

  // Terminator layer — semi-transparent dark fill on the night side
  // wrapLongitude: true tells SolidPolygonLayer to split polygons that cross
  // the ±180° antimeridian, fixing rendering when the night side straddles the date line
  const terminatorLayer = new SolidPolygonLayer({
    id: 'terminator-layer',
    data: [{ polygon: terminatorPolygon }],
    getPolygon: d => d.polygon,
    getFillColor: [0, 0, 30, 128],   // dark blue, 50% transparent
    getLineColor: [50, 80, 160, 100], // subtle blue terminator line
    lineWidthMinPixels: 1,
    stroked: true,
    pickable: false,
    wrapLongitude: true,
  })

  // Build deck.gl layers
  // Layer order matters: tileLayer (basemap/land) first, terminator on top, starfield is background
  const deckLayers = [starfieldLayer, tileLayer, terminatorLayer]

  // Plane layer — directional icons
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
        onClick: (info) => onEntityClick && onEntityClick('plane', info.object),
        billboard: false,
      })
    )
  }

  // Ship layer — directional icons, color-coded by type
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
        onClick: (info) => onEntityClick && onEntityClick('ship', info.object),
        billboard: false,
      })
    )
  }

  // GDELT Events layer — colored scatter points by tone
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
        getRadius: 150000,
        radiusUnits: 'meters',
        onClick: (info) => onEntityClick && onEntityClick('event', info.object),
      })
    )
  }

  // Conflicts layer — GDELT violent events heatmap by tone
  if (layers && layers.conflicts) {
    deckLayers.push(
      new HeatmapLayer({
        id: 'conflicts-layer',
        data: filteredConflicts,
        pickable: true,
        getPosition: d => [d.lon, d.lat],
        getWeight: d => Math.abs(d.tone || 0) + 1,
        intensity: 1,
        threshold: 0.05,
        colorRange: [[255,0,0], [255,80,0], [255,160,0], [255,255,0]],
        onClick: (info) => onEntityClick && onEntityClick('conflict', info.object),
      })
    )
  }

  return (
    <div className="globe-container">
      <DeckGL
        views={new GlobeView({ id: 'globe' })}
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs)}
        controller={true}
        layers={deckLayers}
      />
      <div className="globe-info">
        <span>Planes: {filteredPlanes.length === planes.length ? planes.length : `${filteredPlanes.length} / ${planes.length}`}</span>
        <span>Ships: {filteredShips.length === ships.length ? ships.length : `${filteredShips.length} / ${ships.length}`}</span>
        <span>Events: {filteredEvents.length === events.length ? events.length : `${filteredEvents.length} / ${events.length}`}</span>
        <span>Conflicts: {filteredConflicts.length === conflicts.length ? conflicts.length : `${filteredConflicts.length} / ${conflicts.length}`}</span>
        <span className={`ws-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '\u25CF Live' : '\u25CB Reconnecting'}
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
