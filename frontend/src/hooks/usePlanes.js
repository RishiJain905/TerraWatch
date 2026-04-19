import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { TRAIL_MAX_POINTS } from '../utils/constants'

const initialPlanes = []

const DEFAULT_FILTERS = {
  altitudeMin: 0,
  altitudeMax: 50000,
  callsign: '',
  speedMin: 0,
}

export function usePlanes(selectedPlaneId = null) {
  const [planes, setPlanes] = useState(initialPlanes)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const planesRef = useRef(initialPlanes)
  const selectedPlaneIdRef = useRef(selectedPlaneId)
  const trailStoreRef = useRef({})

  const filteredPlanes = useMemo(() => {
    return planes.filter(plane => {
      const alt = plane.alt ?? 0

      if (alt < filters.altitudeMin) return false
      if (alt > filters.altitudeMax) return false
      if ((plane.speed ?? 0) < filters.speedMin) return false

      if (filters.callsign.trim() !== '') {
        const term = filters.callsign.trim().toLowerCase()
        if (!(plane.callsign ?? '').trim().toLowerCase().includes(term)) return false
      }

      return true
    })
  }, [planes, filters])

  useEffect(() => {
    planesRef.current = planes
  }, [planes])

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => {
      if (key === 'altitudeMin') {
        return {
          ...prev,
          altitudeMin: value,
          altitudeMax: Math.max(prev.altitudeMax, value),
        }
      }
      if (key === 'altitudeMax') {
        return {
          ...prev,
          altitudeMin: Math.min(prev.altitudeMin, value),
          altitudeMax: value,
        }
      }
      return { ...prev, [key]: value }
    })
  }, [])

  const appendSelectedPlaneTrailPoint = useCallback((plane) => {
    if (!plane || !selectedPlaneIdRef.current || plane.id !== selectedPlaneIdRef.current) {
      return
    }

    if (!trailStoreRef.current[plane.id]) {
      trailStoreRef.current[plane.id] = []
    }

    trailStoreRef.current[plane.id].push({
      lon: plane.lon,
      lat: plane.lat,
      timestamp: Date.now(),
    })

    if (trailStoreRef.current[plane.id].length > TRAIL_MAX_POINTS) {
      trailStoreRef.current[plane.id].shift()
    }
  }, [])

  const seedSelectedPlaneTrail = useCallback((plane) => {
    if (!plane || !selectedPlaneIdRef.current || plane.id !== selectedPlaneIdRef.current) {
      trailStoreRef.current = {}
      return
    }

    trailStoreRef.current = {
      [plane.id]: [{
        lon: plane.lon,
        lat: plane.lat,
        timestamp: Date.now(),
      }],
    }
  }, [])

  const fetchPlanes = useCallback(async () => {
    try {
      const res = await fetch('/api/planes')
      if (!res.ok) throw new Error('Failed to fetch planes')
      const data = await res.json()
      setPlanes(data)
      if (selectedPlaneIdRef.current) {
        const selectedPlane = data.find(plane => plane.id === selectedPlaneIdRef.current)
        if (selectedPlane) {
          seedSelectedPlaneTrail(selectedPlane)
        }
      }
      setError(null)
    } catch (e) {
      console.warn('Initial plane fetch failed, WS will populate:', e.message)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [seedSelectedPlaneTrail])

  const addPlane = useCallback((plane) => {
    setPlanes(prev => {
      const existing = prev.findIndex(p => p.id === plane.id)
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = plane
        return updated
      }
      return [...prev, plane]
    })

    appendSelectedPlaneTrailPoint(plane)
  }, [appendSelectedPlaneTrailPoint])

  const addPlanes = useCallback((incomingPlanes) => {
    // plane_batch is authoritative — replace entirely, don't merge
    setPlanes(incomingPlanes)
    if (selectedPlaneIdRef.current) {
      const selectedPlane = incomingPlanes.find(plane => plane.id === selectedPlaneIdRef.current)
      if (selectedPlane) {
        appendSelectedPlaneTrailPoint(selectedPlane)
      }
    }
  }, [appendSelectedPlaneTrailPoint])

  const removePlane = useCallback((planeId) => {
    setPlanes(prev => prev.filter(p => p.id !== planeId))
  }, [])

  useEffect(() => {
    selectedPlaneIdRef.current = selectedPlaneId ?? null

    if (!selectedPlaneIdRef.current) {
      trailStoreRef.current = {}
      return
    }

    const selectedPlane = planesRef.current.find(plane => plane.id === selectedPlaneIdRef.current)
    if (selectedPlane) {
      seedSelectedPlaneTrail(selectedPlane)
      return
    }

    trailStoreRef.current = {}
  }, [selectedPlaneId, seedSelectedPlaneTrail])

  // Initial fetch
  useEffect(() => {
    fetchPlanes()
  }, [fetchPlanes])

  return { planes, filteredPlanes, filters, updateFilter, loading, error, fetchPlanes, addPlane, addPlanes, removePlane, trailStoreRef }
}
