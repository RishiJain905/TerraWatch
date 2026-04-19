export const LAYER_COLORS = {
  plane: [255, 100, 100],
  ship: [100, 200, 255],
  event: [255, 200, 100],
  conflict: [255, 50, 50],
}

export const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

export const TRAIL_MAX_POINTS = 20

export const REFRESH_INTERVALS = {
  planes: 30000,    // 30 seconds
  ships: 60000,    // 60 seconds
  events: 3600000, // 1 hour
}
