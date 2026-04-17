import { useState, useEffect, useCallback, useMemo } from 'react'

const DEFAULT_FILTERS = {
  intensityMin: 0,
}

export function useConflicts() {
  const [conflicts, setConflicts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)

  const fetchConflicts = useCallback(async () => {
    try {
      const res = await fetch('/api/conflicts')
      if (!res.ok) throw new Error('Failed to fetch conflicts')
      const data = await res.json()
      setConflicts(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Single conflict upsert
  const addConflict = useCallback((conflict) => {
    if (!conflict || !conflict.id) return
    setConflicts(prev => {
      const idx = prev.findIndex(c => c.id === conflict.id)
      if (idx >= 0) {
        const updated = [...prev]
        updated[idx] = conflict
        return updated
      }
      return [...prev, conflict]
    })
  }, [])

  // Batch conflict set (for conflict_batch WebSocket messages)
  const addConflicts = useCallback((conflictList) => {
    if (!Array.isArray(conflictList) || conflictList.length === 0) return
    setConflicts(conflictList)
  }, [])

  // Filtered conflicts based on current filters
  const filteredConflicts = useMemo(() => {
    return conflicts.filter(conflict => {
      // Intensity filter (tone-based: Math.abs(tone || 0) + 1 >= intensityMin)
      const intensity = Math.abs(conflict.tone || 0) + 1
      if (intensity < filters.intensityMin) {
        return false
      }

      return true
    })
  }, [conflicts, filters])

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  useEffect(() => {
    fetchConflicts()
  }, [fetchConflicts])

  return { conflicts, filteredConflicts, loading, error, filters, updateFilter, fetchConflicts, addConflict, addConflicts }
}
