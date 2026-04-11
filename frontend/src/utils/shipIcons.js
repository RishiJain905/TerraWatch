// Ship icon generation for deck.gl IconLayer
// Parallel to planeIcons.js — pre-cached SVG icons per ship type category.
// Colors match Phase 3 spec: cargo=blue, tanker=orange, passenger=green, fishing=purple, other=gray

const SHIP_COLORS = {
  cargo:     { fill: '74, 144, 217',  hex: '#4A90D9' },   // blue
  tanker:    { fill: '245, 166, 35',   hex: '#F5A623' },   // orange
  passenger: { fill: '126, 211, 33',   hex: '#7ED321' },   // green
  fishing:   { fill: '144, 19, 254',   hex: '#9013FE' },   // purple
  other:     { fill: '153, 153, 153',  hex: '#999999' },   // gray
}

function createShipSVG(colorFill, shape) {
  let path
  switch (shape) {
    case 'cargo':
      // Large container ship — tall superstructure at stern, containers forward
      path = `<rect x="18" y="24" width="28" height="10" rx="2" fill="rgb(${colorFill})" stroke="white" stroke-width="1.5"/>
              <rect x="38" y="18" width="8" height="16" rx="1" fill="rgb(${colorFill})" stroke="white" stroke-width="1"/>
              <polygon points="10,29 18,24 18,34 10,29" fill="rgb(${colorFill})" stroke="white" stroke-width="1"/>`
      break
    case 'tanker':
      // Wide vessel — rounded hull, bridge at stern
      path = `<ellipse cx="30" cy="29" rx="22" ry="7" fill="rgb(${colorFill})" stroke="white" stroke-width="1.5"/>
              <rect x="40" y="19" width="6" height="14" rx="1.5" fill="rgb(${colorFill})" stroke="white" stroke-width="1"/>
              <rect x="42" y="15" width="2" height="4" fill="white"/>`
      break
    case 'passenger':
      // Ferry/cruise — tall midsection
      path = `<polygon points="8,30 14,22 50,22 56,30 50,36 14,36" fill="rgb(${colorFill})" stroke="white" stroke-width="1.5"/>
              <rect x="24" y="16" width="14" height="8" rx="2" fill="rgb(${colorFill})" stroke="white" stroke-width="1"/>
              <rect x="28" y="10" width="6" height="8" rx="1" fill="rgb(${colorFill})" stroke="white" stroke-width="0.8"/>`
      break
    case 'fishing':
      // Small boat — compact hull, mast
      path = `<polygon points="12,30 18,24 46,24 52,30 46,35 18,35" fill="rgb(${colorFill})" stroke="white" stroke-width="1.5"/>
              <line x1="30" y1="24" x2="30" y2="12" stroke="white" stroke-width="1.5"/>
              <line x1="30" y1="12" x2="40" y2="18" stroke="white" stroke-width="1"/>`
      break
    default:
      // Generic boat shape
      path = `<polygon points="10,30 16,24 48,24 54,30 48,36 16,36" fill="rgb(${colorFill})" stroke="white" stroke-width="1.5"/>
              <rect x="34" y="18" width="6" height="10" rx="1.5" fill="rgb(${colorFill})" stroke="white" stroke-width="1"/>`
  }

  const svgString = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  ${path}
</svg>`

  return `data:image/svg+xml;base64,${btoa(svgString)}`
}

// Pre-cached icon objects — one per ship type category — so IconLayer never
// regenerates identical base64 SVGs on every render / per-ship call.
const CARGO_ICON     = { url: createShipSVG(SHIP_COLORS.cargo.fill, 'cargo'),     width: 64, height: 64, anchorY: 32 }
const TANKER_ICON    = { url: createShipSVG(SHIP_COLORS.tanker.fill, 'tanker'),    width: 64, height: 64, anchorY: 32 }
const PASSENGER_ICON = { url: createShipSVG(SHIP_COLORS.passenger.fill, 'passenger'), width: 64, height: 64, anchorY: 32 }
const FISHING_ICON   = { url: createShipSVG(SHIP_COLORS.fishing.fill, 'fishing'),   width: 64, height: 64, anchorY: 32 }
const OTHER_ICON     = { url: createShipSVG(SHIP_COLORS.other.fill, 'other'),       width: 64, height: 64, anchorY: 32 }

// Map ship_type string → cached icon
const ICON_MAP = {
  cargo:     CARGO_ICON,
  tanker:    TANKER_ICON,
  passenger: PASSENGER_ICON,
  fishing:   FISHING_ICON,
  // Any AIS type not explicitly listed falls through to OTHER
  tug:       OTHER_ICON,
  sailing:   OTHER_ICON,
}

/**
 * Return a cached icon descriptor for the given ship type.
 * Types: cargo, tanker, passenger, fishing, tug, sailing, other (default)
 */
export function getShipIcon(shipType) {
  return ICON_MAP[shipType] || OTHER_ICON
}

/** Color map for legend rendering */
export const SHIP_TYPE_COLORS = SHIP_COLORS
