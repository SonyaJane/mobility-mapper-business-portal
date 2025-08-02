export default function renderMarkers(filtered) {
    // Render businesses on map
    // Remove old markers (MapLibre)
    if (MAP.markers.length) {
    MAP.markers.forEach(m => m.remove());
    }
    MAP.markers = [];
    if (!MAP.map || !filtered) return;
    filtered.forEach((biz, idx) => {
        if (biz.location) {
            if (typeof maplibregl === 'undefined') {
        const container = document.getElementById('accessibility-badges');
        if (!container) return;
            }
        }
    });
}