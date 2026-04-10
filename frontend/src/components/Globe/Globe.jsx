import { useState, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { ScatterplotLayer, IconLayer, BitmapLayer } from '@deck.gl/layers'
import { createPlaneIcon } from '../../utils/planeIcons'
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

const COLORS = {
  plane: [255, 100, 100],
  ship: [100, 200, 255],
}

export default function Globe({ layers, onEntityClick }) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const { planes, addPlane, addPlanes, removePlane } = usePlanes()
  const { ships, addShip } = useShips()

  // Handle WebSocket messages
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
      addShip(msg.data)
    }
  }, [addPlane, addPlanes, addShip, removePlane])

  const { connected } = useWebSocket(handleWSMessage)

  // Tile layer for dark basemap rendered on the globe
  const tileLayer = new TileLayer({
    id: 'base-tiles',
    data: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    minZoom: 0,
    maxZoom: 19,
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
        getIcon: d => ({
          url: createPlaneIcon(d.alt),
          width: 64,
          height: 64,
          anchorY: 32,
        }),
        getPosition: d => [d.lon, d.lat],
        getSize: 48,
        getAngle: d => -(d.heading || 0),
        onClick: (info) => onEntityClick && onEntityClick('plane', info.object),
        billboard: false,
      })
    )
  }

  // Ship layer
  if (layers && layers.ships) {
    deckLayers.push(
      new ScatterplotLayer({
        id: 'ships-layer',
        data: ships,
        pickable: true,
        opacity: 0.9,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 4,
        radiusMaxPixels: 15,
        lineWidthMinPixels: 1,
        getPosition: d => [d.lon, d.lat],
        getRadius: d => 80,
        getFillColor: COLORS.ship,
        getLineColor: [255, 255, 255],
        onClick: (info) => onEntityClick && onEntityClick('ship', info.object),
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
        <div className="legend-item"><span className="legend-dot low"></span>Low (&lt;10k ft)</div>
        <div className="legend-item"><span className="legend-dot medium"></span>Medium (10-30k ft)</div>
        <div className="legend-item"><span className="legend-dot high"></span>High (&gt;30k ft)</div>
      </div>
    </div>
  )
}
