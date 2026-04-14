import { useState, useEffect, useCallback, useMemo } from 'react'

const initialPlanes = []

const DEFAULT_FILTERS = {
  altitudeMin: 0,
  altitudeMax: 50000,
  callsign: '',
  speedMin: 0,
}

export function usePlanes() {
  const [planes, setPlanes] = useState(initialPlanes)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)

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

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  const fetchPlanes = useCallback(async () => {
    try {
      const res = await fetch('/api/planes')
      if (!res.ok) throw new Error('Failed to fetch planes')
      const data = await res.json()
      setPlanes(data)
      setError(null)
    } catch (e) {
      console.warn('Initial plane fetch failed, WS will populate:', e.message)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

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
  }, [])

  const addPlanes = useCallback((incomingPlanes) => {
    // plane_batch is authoritative — replace entirely, don't merge
    setPlanes(incomingPlanes)
  }, [])

  const removePlane = useCallback((planeId) => {
    setPlanes(prev => prev.filter(p => p.id !== planeId))
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchPlanes()
  }, [fetchPlanes])

  return { planes, filteredPlanes, filters, updateFilter, loading, error, fetchPlanes, addPlane, addPlanes, removePlane }
}
