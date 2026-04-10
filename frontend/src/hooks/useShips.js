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

  const addShip = useCallback((ship) => {
    setShips(prev => {
      const existing = prev.findIndex(s => s.id === ship.id)
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = ship
        return updated
      }
      return [...prev, ship]
    })
  }, [])

  const removeShip = useCallback((shipId) => {
    setShips(prev => prev.filter(s => s.id !== shipId))
  }, [])

  useEffect(() => {
    fetchShips()
  }, [fetchShips])

  return { ships, loading, error, fetchShips, addShip, removeShip }
}
