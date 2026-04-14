import { useState, useEffect, useCallback, useMemo } from 'react'

const initialShips = []

const DEFAULT_FILTERS = { types: ['cargo', 'tanker', 'passenger', 'fishing', 'other'], speedMin: 0 }

export function useShips() {
  const [ships, setShips] = useState(initialShips)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)

  const filteredShips = useMemo(() => {
    return ships.filter(ship => {
      const shipType = ship.ship_type || 'other'
      if (!filters.types.includes(shipType)) return false
      if (ship.speed != null && ship.speed < filters.speedMin) return false
      return true
    })
  }, [ships, filters])

  const fetchShips = useCallback(async () => {
    try {
      const res = await fetch('/api/ships')
      if (!res.ok) throw new Error('Failed to fetch ships')
      const data = await res.json()
      setShips(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Single ship upsert
  const addShip = useCallback((ship) => {
    if (!ship || !ship.id) return
    setShips(prev => {
      const idx = prev.findIndex(s => s.id === ship.id)
      if (idx >= 0) {
        const updated = [...prev]
        updated[idx] = ship
        return updated
      }
      return [...prev, ship]
    })
  }, [])

  // Batch ship upsert (for ship_batch WebSocket messages)
  const addShips = useCallback((shipList) => {
    if (!Array.isArray(shipList) || shipList.length === 0) return
    setShips(prev => {
      const map = new Map(prev.map(s => [s.id, s]))
      for (const ship of shipList) {
        if (ship && ship.id) {
          map.set(ship.id, ship)
        }
      }
      return Array.from(map.values())
    })
  }, [])

  // Remove ship by id
  const removeShip = useCallback((shipId) => {
    if (!shipId) return
    setShips(prev => prev.filter(s => s.id !== shipId))
  }, [])

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  useEffect(() => {
    fetchShips()
  }, [fetchShips])

  return { ships, filteredShips, filters, updateFilter, loading, error, fetchShips, addShip, addShips, removeShip }
}
