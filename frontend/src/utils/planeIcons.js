function createPlaneIcon(altitude) {
  let color
  if (altitude < 10000) {
    color = '0, 255, 100'
  } else if (altitude <= 30000) {
    color = '255, 255, 0'
  } else {
    color = '255, 100, 100'
  }

  const svgString = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <polygon points="32,4 44,56 32,48 20,56" fill="rgb(${color})" stroke="white" stroke-width="2"/>
</svg>`

  return `data:image/svg+xml;base64,${btoa(svgString)}`
}

// Pre-computed icon objects — one per altitude band — so IconLayer never
// regenerates identical base64 SVGs on every render / per-plane call.
const LOW_ICON = { url: createPlaneIcon(0), width: 64, height: 64, anchorY: 32 }
const MED_ICON = { url: createPlaneIcon(15000), width: 64, height: 64, anchorY: 32 }
const HIGH_ICON = { url: createPlaneIcon(35000), width: 64, height: 64, anchorY: 32 }

/**
 * Return a cached icon descriptor for the given altitude.
 * Bands: low < 10 000 ft | medium 10 000–30 000 ft | high > 30 000 ft
 */
export function getPlaneIcon(alt) {
  if (alt < 10000) return LOW_ICON
  if (alt < 30000) return MED_ICON
  return HIGH_ICON
}
