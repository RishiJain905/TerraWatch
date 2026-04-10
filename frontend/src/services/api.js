const API_BASE = '/api'

export async function fetchPlanes() {
  const res = await fetch(`${API_BASE}/planes`)
  return res.json()
}

export async function fetchShips() {
  const res = await fetch(`${API_BASE}/ships`)
  return res.json()
}

export async function fetchEvents() {
  const res = await fetch(`${API_BASE}/events`)
  return res.json()
}

export async function fetchMetadata() {
  const res = await fetch(`${API_BASE}/metadata`)
  return res.json()
}
