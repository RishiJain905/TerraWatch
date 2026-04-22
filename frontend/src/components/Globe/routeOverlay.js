function toPosition(point) {
  if (!point) return null
  const lon = Number(point.lon)
  const lat = Number(point.lat)
  if (!Number.isFinite(lon) || !Number.isFinite(lat)) return null
  return [lon, lat]
}

export function buildSelectedPlaneRouteLegs(selectedPlane, selectedPlaneRoute, selectedPlaneRouteStatus) {
  if (selectedPlaneRouteStatus !== 'ok') {
    return []
  }

  const planePosition = toPosition(selectedPlane)
  const departurePosition = toPosition(selectedPlaneRoute?.departure)
  const arrivalPosition = toPosition(selectedPlaneRoute?.arrival)

  if (!planePosition || !departurePosition || !arrivalPosition) {
    return []
  }

  return [
    {
      kind: 'origin',
      sourcePosition: departurePosition,
      targetPosition: planePosition,
    },
    {
      kind: 'destination',
      sourcePosition: planePosition,
      targetPosition: arrivalPosition,
    },
  ]
}
