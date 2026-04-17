import { useState, useCallback, useEffect, useRef } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { IconLayer, BitmapLayer, ScatterplotLayer } from '@deck.gl/layers'
import { getPlaneIcon } from '../../utils/planeIcons'
import { getShipIcon, SHIP_TYPE_COLORS } from '../../utils/shipIcons'
import { useWebSocket } from '../../hooks/useWebSocket'
import { usePlanes } from '../../hooks/usePlanes'
import { useShips } from '../../hooks/useShips'
import { useEvents } from '../../hooks/useEvents'
import { useConflicts } from '../../hooks/useConflicts'
import './Globe.css'

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

  // Build deck.gl layers (draw order: first = bottom). Ships/planes must be LAST so they
  // render on top and win picking — otherwise ScatterplotLayers steal clicks from vessels.
  const deckLayers = [tileLayer]

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
        getRadius: 150000,
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
        getRadius: 165000,
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
    <div className="globe-container">
      <DeckGL
        ref={deckRef}
        views={new GlobeView({ id: 'globe' })}
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs)}
        controller={true}
        layers={deckLayers}
        pickingRadius={36}
        onClick={handleDeckClick}
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
