import { isNightSide } from './terminator.js'

const EARTH_RADIUS_METERS = 6371000
const WEB_MERCATOR_MAX_LAT = 85.0511
const POLE_CENTER_OFFSET = 0.001
const SURFACE_COLOR = [26, 29, 36, 255]
const NIGHT_COLOR = [4, 8, 24, 140]

export const POLAR_CAP_RADIUS_METERS =
  ((90 - WEB_MERCATOR_MAX_LAT) * Math.PI * EARTH_RADIUS_METERS) / 180 + 40000

function buildCap(id, lat, date) {
  const isNight = isNightSide(0, lat > 0 ? 89 : -89, date)

  return {
    id,
    position: [0, lat > 0 ? 90 - POLE_CENTER_OFFSET : -90 + POLE_CENTER_OFFSET],
    radiusMeters: POLAR_CAP_RADIUS_METERS,
    fillColor: isNight ? NIGHT_COLOR : SURFACE_COLOR,
  }
}

export function buildPolarCapData(date = new Date()) {
  return [
    buildCap('north-polar-cap', 90, date),
    buildCap('south-polar-cap', -90, date),
  ]
}
