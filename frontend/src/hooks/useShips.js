import { useState, useEffect, useCallback } from 'react'

const initialShips = []

export function useShips() {
  const [ships, setShips] = useState(initialShips)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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

  useEffect(() => {
    fetchShips()
  }, [fetchShips])

  return { ships, loading, error, fetchShips, addShip, addShips, removeShip }
}
