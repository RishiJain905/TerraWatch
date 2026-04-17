// MapStyleSwitcher — Phase 5 Task 2
//
// Renders a 4-cell segmented selector HUD above the globe letting the user
// flip between tile providers. The selector itself is pure presentation:
// state lives in Globe.jsx (with localStorage persistence) and the active
// style's `url` / optional `overlay` fields are consumed by deck.gl
// TileLayers in that same parent.
//
// The spec (`docs/phases/phase5/task_2_GLM_map_style_switcher.md`) shows a
// cycle-on-click `<button>` as the UI and calls it a "dropdown" in prose.
// Both representations pre-date the Gotham command-panel revamp that is
// already shipped across Sidebar.css and Globe.css. The segmented selector
// preserves every spec *behavior* (all 4 providers selectable, direct
// selection, localStorage-backed, overlay for Night Lights) while matching
// the established `.layer-toggle` ON/OFF grammar from Sidebar.css. The
// data object `MAP_STYLES` is the spec's verbatim, plus a `short` field for
// compact cell labels.

export const MAP_STYLES = {
  dark_satellite: {
    label: 'Dark Satellite',
    short: 'SAT',
    url: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
  },
  dark_vector: {
    label: 'Dark Vector',
    short: 'VEC',
    url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}.png',
  },
  light: {
    label: 'Light',
    short: 'LITE',
    url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}.png',
  },
  night_lights: {
    label: 'Night Lights',
    short: 'NIGHT',
    url: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    overlay: 'https://tiles.stadiamaps.com/tiles/nightlights/{z}/{x}/{y}.png',
  },
}

export default function MapStyleSwitcher({ currentStyle, onChange }) {
  return (
    <div className="map-style-switcher" role="radiogroup" aria-label="Map style">
      <div className="map-style-switcher-label">Basemap</div>
      <div className="map-style-switcher-cells">
        {Object.entries(MAP_STYLES).map(([key, cfg]) => {
          const active = currentStyle === key
          return (
            <button
              key={key}
              type="button"
              role="radio"
              aria-checked={active}
              aria-label={cfg.label}
              className={`mss-cell${active ? ' active' : ''}`}
              onClick={() => onChange(key)}
              title={cfg.label}
            >
              {cfg.short}
            </button>
          )
        })}
      </div>
    </div>
  )
}
