import { useState, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { ScatterplotLayer } from '@deck.gl/layers'
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
  const { planes, addPlane, removePlane } = usePlanes()
  const { ships, addShip } = useShips()

  // Handle WebSocket messages
  const handleWSMessage = useCallback((msg) => {
    if (msg.type === 'plane') {
      if (msg.action === 'remove' && msg.data?.id) {
        removePlane(msg.data.id)
        return
      }
      addPlane(msg.data)
    } else if (msg.type === 'ship') {
      addShip(msg.data)
    }
  }, [addPlane, addShip, removePlane])

  const { connected } = useWebSocket(handleWSMessage)

  // Tile layer for dark basemap rendered on the globe
  const tileLayer = new TileLayer({
    id: 'base-tiles',
    data: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    minZoom: 0,
    maxZoom: 19,
    tileSize: 256,
    pickable: false,
  })

  // Build deck.gl layers
  const deckLayers = [tileLayer]

  // Plane layer
  if (layers && layers.planes) {
    deckLayers.push(
      new ScatterplotLayer({
        id: 'planes-layer',
        data: planes,
        pickable: true,
        opacity: 0.9,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 4,
        radiusMaxPixels: 20,
        lineWidthMinPixels: 1,
        getPosition: d => [d.lon, d.lat],
        getRadius: d => 100,
        getFillColor: COLORS.plane,
        getLineColor: [255, 255, 255],
        onClick: (info) => onEntityClick && onEntityClick('plane', info.object),
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
    </div>
  )
}
