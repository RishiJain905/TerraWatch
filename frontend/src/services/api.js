const API_BASE = import.meta.env.VITE_API_URL ?? ''

export async function fetchPlanes() {
  const res = await fetch(`${API_BASE}/api/planes`)
  if (!res.ok) throw new Error('Failed to fetch planes')
  return res.json()
}

export async function fetchShips() {
  const res = await fetch(`${API_BASE}/api/ships`)
  if (!res.ok) throw new Error('Failed to fetch ships')
  return res.json()
}

export async function fetchEvents() {
  const res = await fetch(`${API_BASE}/api/events`)
  if (!res.ok) throw new Error('Failed to fetch events')
  return res.json()
}

export async function fetchMetadata() {
  const res = await fetch(`${API_BASE}/api/metadata`)
  if (!res.ok) throw new Error('Failed to fetch metadata')
  return res.json()
}

export async function fetchConflicts() {
  const res = await fetch(`${API_BASE}/api/conflicts`)
  if (!res.ok) throw new Error('Failed to fetch conflicts')
  return res.json()
}
