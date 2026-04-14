import { useState, useEffect, useCallback, useMemo } from 'react'

const DEFAULT_FILTERS = {
  categories: [
    'diplomacy',
    'material_help',
    'train',
    'yield',
    'demonstrate',
    'assault',
    'fight',
    'unconventional_mass_gvc',
    'conventional_mass_gvc',
    'force_range',
    'protest',
    'government_debate',
    'rioting',
    'disaster',
    'health',
    'weather',
  ],
  toneMin: -10,
  toneMax: 10,
  dateRange: 'all',
}

export function useEvents() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)

  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch('/api/events')
      if (!res.ok) throw new Error('Failed to fetch events')
      const data = await res.json()
      setEvents(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Single event upsert
  const addEvent = useCallback((event) => {
    if (!event || !event.id) return
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

  // Batch event set (for event_batch WebSocket messages)
  const addEvents = useCallback((eventList) => {
    if (!Array.isArray(eventList) || eventList.length === 0) return
    setEvents(eventList)
  }, [])

  // Filtered events based on current filters
  const filteredEvents = useMemo(() => {
    const now = Date.now()

    return events.filter(event => {
      // Category filter — exclude events with empty category
      if (!event.category || !filters.categories.includes(event.category)) {
        return false
      }

      // Tone range filter
      const tone = event.tone || 0
      if (tone < filters.toneMin || tone > filters.toneMax) {
        return false
      }

      // Date range filter
      if (filters.dateRange !== 'all') {
        if (!event.date) return false
        const eventDate = new Date(event.date + 'T00:00:00Z').getTime()
        if (Number.isNaN(eventDate)) return false
        let cutoff
        switch (filters.dateRange) {
          case '24h':
            cutoff = now - 86400000
            break
          case '48h':
            cutoff = now - 172800000
            break
          case '7d':
            cutoff = now - 604800000
            break
          default:
            cutoff = 0
        }
        if (eventDate < cutoff) {
          return false
        }
      }

      return true
    })
  }, [events, filters])

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => {
      const clampTone = (tone) => Math.min(10, Math.max(-10, tone))

      if (key === 'toneMin') {
        const nextToneMin = clampTone(Number(value))
        if (!Number.isFinite(nextToneMin)) return prev
        return { ...prev, toneMin: Math.min(nextToneMin, prev.toneMax) }
      }

      if (key === 'toneMax') {
        const nextToneMax = clampTone(Number(value))
        if (!Number.isFinite(nextToneMax)) return prev
        return { ...prev, toneMax: Math.max(nextToneMax, prev.toneMin) }
      }

      return { ...prev, [key]: value }
    })
  }, [])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  return { events, filteredEvents, loading, error, filters, updateFilter, fetchEvents, addEvent, addEvents }
}
