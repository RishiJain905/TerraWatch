import { useState, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { IconLayer, BitmapLayer } from '@deck.gl/layers'
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
    }
  }, [addPlane, addPlanes, addShip, addShips, removePlane, removeShip])

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
