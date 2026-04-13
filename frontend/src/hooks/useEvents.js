import { useState, useEffect, useCallback } from 'react'

export function useEvents() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Single event upsert by id
  const addEvent = useCallback((event) => {
    if (!event?.id) return
    setEvents(prev => {
      const idx = prev.findIndex(e => e.id === event.id)
      if (idx >= 0) {
        const updated = [...prev]
        updated[idx] = event
        return updated
      }
      return [...prev, event]
    })
  }, [])

  // Batch upsert — authoritative, replaces state
  const addEvents = useCallback((incoming) => {
    if (!Array.isArray(incoming)) return
    setEvents(incoming)
  }, [])

  // Remove event by id
  const removeEvent = useCallback((id) => {
    setEvents(prev => prev.filter(e => e.id !== id))
  }, [])

  // Initial REST fetch for SSR / initial load
  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch('/api/events')
      if (!res.ok) throw new Error('Failed to fetch events')
      const data = await res.json()
      setEvents(data)
      setError(null)
    } catch (e) {
      console.warn('Initial events fetch failed, WS will populate:', e.message)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  return { events, loading, error, fetchEvents, addEvent, addEvents, removeEvent }
}
