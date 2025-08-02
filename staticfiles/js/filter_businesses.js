export default function filterBusinesses() {
        const search = document.getElementById('business-search').value;
        // Use mobile panel selects if visible, otherwise desktop
        let access;
        const mobileFilters = document.getElementById('mobile-filters');
        if (mobileFilters && mobileFilters.style.display !== 'none') {
            // allow multiple mobile selections
            const accessSelect = document.getElementById('accessibility-select-mobile-panel');
            access = Array.from(accessSelect.selectedOptions)
                .map(o => o.value)
                .filter(v => v);
        } else {
            // desktop multi-select
            access = Array.from(document.getElementById('accessibility-select').selectedOptions)
                .map(o => o.value)
                .filter(v => v);
        }
        if (!search && Array.isArray(access) && access.length === 0) {
            // No search/filter: show only the map, clear results
            renderMarkers([]);
            renderResults([]);
            return;
        }
        // Build query params to include multiple accessibility filters
        const params = new URLSearchParams();
        if (search) params.append('q', search);
        access.forEach(feature => params.append('accessibility', feature));
        fetch(`/business/ajax/search-businesses/?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            businesses = data.businesses || [];
            // Render markers and results
            renderMarkers(businesses);
            renderResults(businesses);
        });
    }