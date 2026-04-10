import { useState, useEffect, useCallback } from 'react'

const initialPlanes = []

export function usePlanes() {
  const [planes, setPlanes] = useState(initialPlanes)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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
    setPlanes(prev => {
      const map = new Map(prev.map(p => [p.id, p]))
      for (const plane of incomingPlanes) {
        map.set(plane.id, plane)
      }
      return Array.from(map.values())
    })
  }, [])

  const removePlane = useCallback((planeId) => {
    setPlanes(prev => prev.filter(p => p.id !== planeId))
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchPlanes()
  }, [fetchPlanes])

  return { planes, loading, error, fetchPlanes, addPlane, addPlanes, removePlane }
}
