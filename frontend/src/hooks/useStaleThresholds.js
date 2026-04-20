import { useState, useEffect } from 'react'

const DEFAULT_THRESHOLDS = {
  planes: 300,
  ships: 600,
  events: 3600,
  conflicts: 3600,
}

export function useStaleThresholds() {
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS)

  useEffect(() => {
    let cancelled = false
    fetch('/api/stale-thresholds')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => {
        if (!cancelled && data) {
          setThresholds({
            planes: data.planes ?? DEFAULT_THRESHOLDS.planes,
            ships: data.ships ?? DEFAULT_THRESHOLDS.ships,
            events: data.events ?? DEFAULT_THRESHOLDS.events,
            conflicts: data.conflicts ?? DEFAULT_THRESHOLDS.conflicts,
          })
        }
      })
      .catch(() => {}) // keep defaults
    return () => { cancelled = true }
  }, [])

  return thresholds
}
