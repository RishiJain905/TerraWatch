const SHIP_TRAIL_COLOR_RGB = [88, 196, 220]
const SHIP_TRAIL_ALPHA_MIN = 80
const SHIP_TRAIL_ALPHA_MAX = 220

export function buildShipTrailPath(points, livePosition = null) {
  const path = Array.isArray(points)
    ? points
      .filter(point => point && Number.isFinite(point.lon) && Number.isFinite(point.lat))
      .map(point => [point.lon, point.lat])
    : []

  if (
    livePosition &&
    Number.isFinite(livePosition.lon) &&
    Number.isFinite(livePosition.lat)
  ) {
    const lastPoint = path[path.length - 1]
    if (
      !lastPoint ||
      lastPoint[0] !== livePosition.lon ||
      lastPoint[1] !== livePosition.lat
    ) {
      path.push([livePosition.lon, livePosition.lat])
    }
  }

  return path
}

export function buildShipTrailSegments(points, livePosition = null) {
  const path = buildShipTrailPath(points, livePosition)
  if (path.length < 2) {
    return []
  }

  const segmentCount = path.length - 1

  return path.flatMap((point, index) => {
    if (index === 0) {
      return []
    }

    const previousPoint = path[index - 1]
    if (!previousPoint || !point) {
      return []
    }

    if (
      previousPoint[0] === point[0] &&
      previousPoint[1] === point[1]
    ) {
      return []
    }

    const sourceAlpha = Math.round(
      SHIP_TRAIL_ALPHA_MIN + ((SHIP_TRAIL_ALPHA_MAX - SHIP_TRAIL_ALPHA_MIN) * (index - 1)) / segmentCount
    )
    const targetAlpha = Math.round(
      SHIP_TRAIL_ALPHA_MIN + ((SHIP_TRAIL_ALPHA_MAX - SHIP_TRAIL_ALPHA_MIN) * index) / segmentCount
    )

    return [{
      sourcePosition: previousPoint,
      targetPosition: point,
      sourceColor: [...SHIP_TRAIL_COLOR_RGB, sourceAlpha],
      targetColor: [...SHIP_TRAIL_COLOR_RGB, targetAlpha],
    }]
  })
}
