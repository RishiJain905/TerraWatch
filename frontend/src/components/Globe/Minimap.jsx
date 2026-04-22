import { useMemo } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { BitmapLayer, ScatterplotLayer } from '@deck.gl/layers'

export default function Minimap({ viewState, basemapUrl, overlayUrl }) {
  const minimapViewState = useMemo(
    () => ({
      longitude: viewState.longitude,
      latitude: viewState.latitude,
      zoom: 1,
      pitch: 0,
      bearing: 0,
    }),
    [viewState.longitude, viewState.latitude],
  )

  const layers = [
    // Basemap tiles — same renderSubLayers → BitmapLayer pattern as the main globe
    new TileLayer({
      id: 'minimap-base-tiles',
      data: basemapUrl,
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
    }),

    // Optional overlay tiles (e.g. night lights)
    ...(overlayUrl
      ? [
          new TileLayer({
            id: 'minimap-overlay-tiles',
            data: overlayUrl,
            minZoom: 0,
            maxZoom: 10,
            tileSize: 256,
            pickable: false,
            opacity: 0.85,
            renderSubLayers: (props) => {
              const { boundingBox } = props.tile
              return new BitmapLayer(props, {
                data: undefined,
                image: props.data,
                bounds: [boundingBox[0][0], boundingBox[0][1], boundingBox[1][0], boundingBox[1][1]],
              })
            },
          }),
        ]
      : []),

    // View-center indicator dot — accent-air color
    new ScatterplotLayer({
      id: 'minimap-indicator',
      data: [{ longitude: viewState.longitude, latitude: viewState.latitude }],
      getPosition: (d) => [d.longitude, d.latitude],
      getFillColor: [232, 184, 74, 255], // --accent-air
      getRadius: 50000,
      radiusUnits: 'meters',
      pickable: false,
    }),
  ]

  return (
    <div className="minimap-container" aria-hidden="true">
      <DeckGL
        views={new GlobeView({ id: 'minimap-globe' })}
        viewState={minimapViewState}
        controller={false}
        layers={layers}
      />
    </div>
  )
}
