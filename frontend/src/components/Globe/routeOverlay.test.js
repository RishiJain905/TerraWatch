import test from 'node:test'
import assert from 'node:assert/strict'

import { buildSelectedPlaneRouteLegs } from './routeOverlay.js'

test('buildSelectedPlaneRouteLegs returns two legs for a fully resolved route', () => {
  const legs = buildSelectedPlaneRouteLegs(
    { lon: -73.7781, lat: 40.6413 },
    {
      departure: { lon: -0.4543, lat: 51.4700 },
      arrival: { lon: 2.5559, lat: 49.0097 },
    },
    'ok'
  )

  assert.deepEqual(legs, [
    {
      kind: 'origin',
      sourcePosition: [-0.4543, 51.47],
      targetPosition: [-73.7781, 40.6413],
    },
    {
      kind: 'destination',
      sourcePosition: [-73.7781, 40.6413],
      targetPosition: [2.5559, 49.0097],
    },
  ])
})

test('buildSelectedPlaneRouteLegs returns no legs unless the route is ok', () => {
  assert.deepEqual(
    buildSelectedPlaneRouteLegs(
      { lon: 1, lat: 2 },
      { departure: { lon: 3, lat: 4 }, arrival: { lon: 5, lat: 6 } },
      'loading'
    ),
    []
  )
})

test('buildSelectedPlaneRouteLegs returns no legs when airport coordinates are missing', () => {
  assert.deepEqual(
    buildSelectedPlaneRouteLegs(
      { lon: 1, lat: 2 },
      { departure: { iata: 'JFK' }, arrival: { lon: 5, lat: 6 } },
      'ok'
    ),
    []
  )
})
