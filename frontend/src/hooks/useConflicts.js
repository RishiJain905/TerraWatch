import { useState, useEffect, useCallback } from 'react'

export function useConflicts() {
  const [conflicts, setConflicts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Single conflict upsert by id
  const addConflict = useCallback((conflict) => {
    if (!conflict?.id) return
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

  // Batch upsert — authoritative, replaces state
  const addConflicts = useCallback((incoming) => {
    if (!Array.isArray(incoming)) return
    setConflicts(incoming)
  }, [])

  // Remove conflict by id
  const removeConflict = useCallback((id) => {
    setConflicts(prev => prev.filter(c => c.id !== id))
  }, [])

  // Initial REST fetch for SSR / initial load
  const fetchConflicts = useCallback(async () => {
    try {
      const res = await fetch('/api/conflicts')
      if (!res.ok) throw new Error('Failed to fetch conflicts')
      const data = await res.json()
      setConflicts(data)
      setError(null)
    } catch (e) {
      console.warn('Initial conflicts fetch failed, WS will populate:', e.message)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchConflicts() }, [fetchConflicts])

  return { conflicts, loading, error, fetchConflicts, addConflict, addConflicts, removeConflict }
}
