import { useState, useCallback, useEffect } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { IconLayer, BitmapLayer, ScatterplotLayer } from '@deck.gl/layers'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import { getPlaneIcon } from '../../utils/planeIcons'
import { getShipIcon, SHIP_TYPE_COLORS } from '../../utils/shipIcons'
import { useWebSocket } from '../../hooks/useWebSocket'
import { usePlanes } from '../../hooks/usePlanes'
import { useShips } from '../../hooks/useShips'
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

export default function Globe({ layers, onEntityClick }) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const [events, setEvents] = useState([])
  const [conflicts, setConflicts] = useState([])
  const { planes, addPlane, addPlanes, removePlane } = usePlanes()
  const { ships, addShip, addShips, removeShip } = useShips()

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
      if (msg.data && Array.isArray(msg.data)) { setEvents(msg.data) }
    } else if (msg.type === 'conflict_batch') {
      if (msg.data && Array.isArray(msg.data)) { setConflicts(msg.data) }
    }
  }, [addPlane, addPlanes, addShip, addShips, removePlane, removeShip])

  const { connected } = useWebSocket(handleWSMessage)

  // Initial REST fetch for events and conflicts on mount
  useEffect(() => {
    fetch('/api/events')
      .then(r => r.ok ? r.json() : [])
      .then(data => { if (Array.isArray(data) && data.length > 0) setEvents(data) })
      .catch(() => {})
    fetch('/api/conflicts')
      .then(r => r.ok ? r.json() : [])
      .then(data => { if (Array.isArray(data) && data.length > 0) setConflicts(data) })
      .catch(() => {})
  }, [])

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

  // Build deck.gl layers
  const deckLayers = [tileLayer]

  // Plane layer — directional icons
  if (layers && layers.planes) {
    deckLayers.push(
      new IconLayer({
        id: 'planes-layer',
        data: planes,
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
        data: ships,
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
        data: events,
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
        data: conflicts,
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
        <span>Planes: {planes.length}</span>
        <span>Ships: {ships.length}</span>
        <span>Events: {events.length}</span>
        <span>Conflicts: {conflicts.length}</span>
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
