export default function renderMarkers(businesses) {
    // Render businesses on map
    // Remove old markers (MapLibre)
    if (MAP.markers.length) {
        MAP.markers.forEach(m => m.remove());
    }
    MAP.markers = [];
    if (!MAP.map || !businesses) return;
    businesses.forEach((biz, idx) => {
        if (biz.location) {
            const { lat, lng } = biz.location;
            // Prepare popup content by reusing the list item HTML
            let popupContent = biz.business_name || '';
            const listItem = document.querySelector(`#results-list li[data-id="${biz.id}"]`);
            if (listItem) {
                // Clone the list item and remove the toggle arrow before injecting
                const clone = listItem.cloneNode(true);
                const arrow = clone.querySelector('.toggle-arrow');
                if (arrow) arrow.remove();
                popupContent = clone.innerHTML;
            }
            // Append a link to show more info in an overlay
            popupContent += `<div><a href="#" data-id="${biz.id}" class="show-more-info">Show more info</a></div>`;
            // Create a marker at the business location with a popup
            const marker = new maplibregl.Marker()
                .setLngLat([lng, lat])
                .setPopup(
                    new maplibregl.Popup({ offset: 25 })
                        .setHTML(popupContent)
                )
                .addTo(MAP.map);
            // Keep track for removal
            MAP.markers.push(marker);
        }
    });
}