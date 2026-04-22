import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPlaneTrailPath, buildPlaneTrailSegments } from './planeTrail.js'

test('buildPlaneTrailSegments returns one visible segment for two trail points', () => {
  const segments = buildPlaneTrailSegments([
    { lon: -15.8117, lat: 12.3052 },
    { lon: -15.8299, lat: 12.3276 },
  ])

  assert.equal(segments.length, 1)
  assert.deepEqual(segments[0].sourcePosition, [-15.8117, 12.3052])
  assert.deepEqual(segments[0].targetPosition, [-15.8299, 12.3276])
  assert.equal(segments[0].sourceColor[3] < segments[0].targetColor[3], true)
})

test('buildPlaneTrailSegments returns consecutive segments for longer trails', () => {
  const segments = buildPlaneTrailSegments([
    { lon: 1, lat: 2 },
    { lon: 3, lat: 4 },
    { lon: 5, lat: 6 },
  ])

  assert.equal(segments.length, 2)
  assert.deepEqual(
    segments.map(({ sourcePosition, targetPosition }) => ({
      sourcePosition,
      targetPosition,
    })),
    [
      { sourcePosition: [1, 2], targetPosition: [3, 4] },
      { sourcePosition: [3, 4], targetPosition: [5, 6] },
    ]
  )
})

test('buildPlaneTrailPath appends the live selected-plane position when it has advanced', () => {
  const path = buildPlaneTrailPath(
    [
      { lon: -15.8117, lat: 12.3052 },
      { lon: -15.8299, lat: 12.3276 },
    ],
    { lon: -15.845, lat: 12.358 }
  )

  assert.deepEqual(path, [
    [-15.8117, 12.3052],
    [-15.8299, 12.3276],
    [-15.845, 12.358],
  ])
})

test('buildPlaneTrailPath does not duplicate the live selected-plane position', () => {
  const path = buildPlaneTrailPath(
    [
      { lon: 1, lat: 2 },
      { lon: 3, lat: 4 },
    ],
    { lon: 3, lat: 4 }
  )

  assert.deepEqual(path, [
    [1, 2],
    [3, 4],
  ])
})
