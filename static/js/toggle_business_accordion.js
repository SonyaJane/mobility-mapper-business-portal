export default function toggleBusinessAccordion(li, infoPanel, arrowIcon, biz) {
    // Get all results in the list
    const allResults = document.querySelectorAll('#results-list > li');
    // Find the marker for this business by coordinates
    const highlightMarker = MAP.markers.find(m => {
        const pt = m.getLngLat();
        return pt.lng === biz.location.lng && pt.lat === biz.location.lat;
    });
    // If the clicked panel is already open, close it
    if (infoPanel.classList.contains('show')) {
        infoPanel.classList.remove('show');
        infoPanel.classList.add('hide');
        // Reset the arrow icon to down
        if (arrowIcon) {
            arrowIcon.classList.remove('bi-chevron-up');
            arrowIcon.classList.add('bi-chevron-down');
        }
        // Show all results again and remove highlight class
        allResults.forEach(result => {
            result.classList.remove('hide');
            result.classList.remove('single-visible');
        });
        // Remove any marker highlight when closing
        if (Array.isArray(MAP.markers)) {
            MAP.markers.forEach(marker => {
                marker.getElement().classList.remove('highlighted-marker');
            });
        }
    } else { 
        // If the clicked panel is not open, open it
        // First, close any other open panels and remove their highlights
        const openPanels = document.querySelectorAll('.accordion-collapse.show');
        openPanels.forEach(panel => {
            panel.classList.remove('show');
            panel.classList.remove('single-visible');
            panel.classList.add('hide');
        });
        // Reset all arrow icons to down
        const allArrows = document.querySelectorAll('.toggle-arrow');
        allArrows.forEach(icon => {
            icon.classList.remove('bi-chevron-up');
            icon.classList.add('bi-chevron-down');
        });
        // Now open the clicked panel
        infoPanel.classList.remove('hide');
        infoPanel.classList.add('show');
        // Set the arrow icon to up
        if (arrowIcon) {
            arrowIcon.classList.remove('bi-chevron-down');
            arrowIcon.classList.add('bi-chevron-up');
        }
        // Hide all other results except this one, and add highlight
        allResults.forEach(result => {
            result.classList.remove('single-visible');
            if (result !== li) {
                result.classList.add('hide');
            } else {
                result.classList.add('single-visible');
            }
        });
        // On desktop, fly to and highlight the corresponding marker
        if (window.matchMedia('(min-width: 768px)').matches && biz.location && MAP.map && Array.isArray(MAP.markers)) {
            // Center and zoom map on business location
            MAP.map.flyTo({ center: [biz.location.lng, biz.location.lat], zoom: 16 });
            // Clear previous marker highlights
            MAP.markers.forEach(marker => {
                marker.getElement().classList.remove('highlighted-marker');
            });
            if (highlightMarker) {
                highlightMarker.getElement().classList.add('highlighted-marker');
            }
        }
        // 
    }
}