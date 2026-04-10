import { useState, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import './Globe.css'

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

export default function Globe() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)

  const onViewStateChange = useCallback(({ viewState: vs }) => {
    setViewState(vs)
  }, [])

  // Tile layer for dark basemap rendered on the globe
  const tileLayer = new TileLayer({
    id: 'base-tiles',
    data: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    minZoom: 0,
    maxZoom: 19,
    tileSize: 256,
    pickable: false,
  })

  const layers = [tileLayer]

  return (
    <div className="globe-container">
      <DeckGL
        views={new GlobeView({ id: 'globe' })}
        viewState={viewState}
        onViewStateChange={onViewStateChange}
        controller={true}
        layers={layers}
      />
    </div>
  )
}
