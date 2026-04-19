import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { TRAIL_MAX_POINTS } from '../utils/constants'

const initialShips = []

const DEFAULT_FILTERS = { types: ['cargo', 'tanker', 'passenger', 'fishing', 'other'], speedMin: 0 }

export function useShips(selectedShipId = null) {
  const [ships, setShips] = useState(initialShips)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const shipsRef = useRef(initialShips)
  const selectedShipIdRef = useRef(selectedShipId)
  const trailStoreRef = useRef({})

  const filteredShips = useMemo(() => {
    return ships.filter(ship => {
      const shipType = ship.ship_type || 'other'
      if (!filters.types.includes(shipType)) return false
      if (ship.speed != null && ship.speed < filters.speedMin) return false
      return true
    })
  }, [ships, filters])

  useEffect(() => {
    shipsRef.current = ships
  }, [ships])

  const appendSelectedShipTrailPoint = useCallback((ship) => {
    if (!ship || !selectedShipIdRef.current || ship.id !== selectedShipIdRef.current) {
      return
    }

    if (!trailStoreRef.current[ship.id]) {
      trailStoreRef.current[ship.id] = []
    }

    trailStoreRef.current[ship.id].push({
      lon: ship.lon,
      lat: ship.lat,
      timestamp: Date.now(),
    })

    if (trailStoreRef.current[ship.id].length > TRAIL_MAX_POINTS) {
      trailStoreRef.current[ship.id].shift()
    }
  }, [])

  const seedSelectedShipTrail = useCallback((ship) => {
    if (!ship || !selectedShipIdRef.current || ship.id !== selectedShipIdRef.current) {
      trailStoreRef.current = {}
      return
    }

    trailStoreRef.current = {
      [ship.id]: [{
        lon: ship.lon,
        lat: ship.lat,
        timestamp: Date.now(),
      }],
    }
  }, [])

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
    appendSelectedShipTrailPoint(ship)
  }, [appendSelectedShipTrailPoint])

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
    // Clean up trail entries for ship IDs no longer in the batch
    const batchIds = new Set(shipList.filter(s => s && s.id).map(s => s.id))
    for (const id of Object.keys(trailStoreRef.current)) {
      if (!batchIds.has(id)) {
        delete trailStoreRef.current[id]
      }
    }
    if (selectedShipIdRef.current) {
      const selectedShip = shipList.find(ship => ship && ship.id === selectedShipIdRef.current)
      if (selectedShip) {
        appendSelectedShipTrailPoint(selectedShip)
      }
    }
  }, [appendSelectedShipTrailPoint])

  // Remove ship by id
  const removeShip = useCallback((shipId) => {
    if (!shipId) return
    setShips(prev => prev.filter(s => s.id !== shipId))
    delete trailStoreRef.current[shipId]
  }, [])

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  useEffect(() => {
    fetchShips()
  }, [fetchShips])

  useEffect(() => {
    selectedShipIdRef.current = selectedShipId ?? null

    if (!selectedShipIdRef.current) {
      trailStoreRef.current = {}
      return
    }

    const selectedShip = shipsRef.current.find(ship => ship.id === selectedShipIdRef.current)
    if (selectedShip) {
      seedSelectedShipTrail(selectedShip)
      return
    }

    trailStoreRef.current = {}
  }, [selectedShipId, seedSelectedShipTrail])

  return { ships, filteredShips, filters, updateFilter, loading, error, fetchShips, addShip, addShips, removeShip, trailStoreRef }
}
