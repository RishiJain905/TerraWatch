/**
 * terminator.js — Solar terminator calculations for TerraWatch.
 *
 * Provides:
 *   getTerminatorPolygon(date) → [lon, lat][] — single night-side polygon
 *   isNightSide(lon, lat, date) → boolean
 *
 * The polygon is returned in [-180, 180] longitude range. When it crosses
 * the antimeridian (±180°), SolidPolygonLayer with `wrapLongitude: true`
 * will automatically split it for correct rendering.
 *
 * Uses NOAA solar equations for declination and subsolar point.
 */

const DEG = Math.PI / 180
const RAD = 180 / Math.PI

// ── Solar position helpers ────────────────────────────────────────────────

function getDayOfYear(date) {
  const start = new Date(date.getUTCFullYear(), 0, 0)
  return Math.floor((date - start) / 86400000) + 1
}

function getSolarDeclination(date) {
  const doy = getDayOfYear(date)
  return -23.45 * DEG * Math.cos((2 * Math.PI / 365) * (doy + 10))
}

function getSubsolarLongitude(date) {
  const hours = date.getUTCHours() + date.getUTCMinutes() / 60 + date.getUTCSeconds() / 3600
  return (12 - hours) * 15
}

function solarElevationSin(lonDeg, latDeg, decRad, subSolarLonDeg) {
  const latRad = latDeg * DEG
  const hourAngle = (lonDeg - subSolarLonDeg) * DEG
  return (
    Math.sin(latRad) * Math.sin(decRad) +
    Math.cos(latRad) * Math.cos(decRad) * Math.cos(hourAngle)
  )
}

function isNight(lonDeg, latDeg, decRad, subSolarLonDeg) {
  return solarElevationSin(lonDeg, latDeg, decRad, subSolarLonDeg) < 0
}

/** Normalize longitude to [-180, 180] */
function normalizeLon(lon) {
  return ((lon % 360) + 540) % 360 - 180
}

// ── Terminator crossing finder ───────────────────────────────────────────

/**
 * Find day→night and night→day longitude crossings at a given latitude.
 * Scans full 360° of longitude and binary-searches each crossing.
 *
 * @returns {{lon: number, type: string}[]} 0 or 2 crossings
 */
function findTerminatorCrossings(latDeg, decRad, subSolarLonDeg) {
  if (Math.abs(latDeg) >= 90) return []

  const N = 720
  const crossings = []
  let prevNight = isNight(-180, latDeg, decRad, subSolarLonDeg)

  for (let i = 1; i <= N; i++) {
    const lon = -180 + (i / N) * 360
    const night = isNight(lon, latDeg, decRad, subSolarLonDeg)
    if (prevNight !== night) {
      // Binary search
      let lo = -180 + ((i - 1) / N) * 360
      let hi = lon
      for (let j = 0; j < 50; j++) {
        const mid = (lo + hi) / 2
        if (isNight(lo, latDeg, decRad, subSolarLonDeg) ===
            isNight(mid, latDeg, decRad, subSolarLonDeg)) lo = mid
        else hi = mid
      }
      const crossLon = (lo + hi) / 2
      const wasNight = isNight(lo, latDeg, decRad, subSolarLonDeg)
      crossings.push({ lon: crossLon, type: wasNight ? 'nightToDay' : 'dayToNight' })
      prevNight = night
    }
  }
  return crossings
}

// ── Public API ────────────────────────────────────────────────────────────

/**
 * Generate a polygon covering the night side of the Earth.
 *
 * Traces the terminator by finding latitude-by-latitude day→night and
 * night→day crossings. The polygon is built in two passes:
 *   1. East edge (night→day boundary) from N→S
 *   2. West edge (day→night boundary) from S→N
 * with pole closure if the pole is in darkness.
 *
 * The result is a single polygon in [-180, 180] range. When it crosses
 * the antimeridian, use `wrapLongitude: true` on SolidPolygonLayer to
 * render correctly.
 *
 * @param {Date} date — UTC date
 * @returns {Array<[number, number]>} polygon coordinates [lon, lat][]
 */
export function getTerminatorPolygon(date = new Date()) {
  const decRad = getSolarDeclination(date)
  const subSolarLon = getSubsolarLongitude(date)
  const step = 2

  // Collect terminator crossing points at each latitude
  const eastEdge = [] // night→day boundary
  const westEdge = [] // day→night boundary

  for (let lat = 89; lat >= -89; lat -= step) {
    const xings = findTerminatorCrossings(lat, decRad, subSolarLon)
    if (xings.length === 2) {
      const dtn = xings.find(x => x.type === 'dayToNight')
      const ntd = xings.find(x => x.type === 'nightToDay')
      if (dtn && ntd) {
        eastEdge.push({ lon: ntd.lon, lat })
        westEdge.push({ lon: dtn.lon, lat })
      }
    }
    // 0 crossings = polar day or polar night (no terminator at this lat)
  }

  if (eastEdge.length < 4) return []

  // Check pole darkness
  const southPoleDark = isNight(subSolarLon + 180, -89.9, decRad, subSolarLon)
  const northPoleDark = isNight(subSolarLon + 180, 89.9, decRad, subSolarLon)

  // Build polygon: east edge → south → west edge (reversed) → north → close
  const poly = []

  // East edge N→S (night→day boundary)
  for (const pt of eastEdge) poly.push([normalizeLon(pt.lon), pt.lat])

  // South closure
  if (southPoleDark) {
    poly.push([normalizeLon(eastEdge[eastEdge.length - 1].lon), -90])
    poly.push([normalizeLon(westEdge[westEdge.length - 1].lon), -90])
  }
  // If south pole is lit (midnight sun), the terminator circles the pole —
  // the two edges already meet at the extremal latitude

  // West edge S→N (day→night boundary)
  for (let i = westEdge.length - 1; i >= 0; i--) {
    poly.push([normalizeLon(westEdge[i].lon), westEdge[i].lat])
  }

  // North closure
  if (northPoleDark) {
    poly.push([normalizeLon(westEdge[0].lon), 90])
    poly.push([normalizeLon(eastEdge[0].lon), 90])
  }

  // Close ring
  poly.push(poly[0])

  return poly
}

/**
 * True if the given point is on the night side of the Earth.
 */
export function isNightSide(lonDeg, latDeg, date = new Date()) {
  const decRad = getSolarDeclination(date)
  const subSolarLon = getSubsolarLongitude(date)
  return isNight(lonDeg, latDeg, decRad, subSolarLon)
}