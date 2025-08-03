import renderResultsList from './render_results_list.js';
import renderMarkers from './render_markers.js';

export default function filterBusinesses() {
    // Get the search input value
    const search = document.getElementById('business-search').value;
   
    // Get accessibility filter selections
    // Use mobile panel filter selections if visible, otherwise desktop 
    const mobileFilters = document.getElementById('mobile-filters');

    let access;
    // If mobile filters are visible, use mobile panel selections
    // otherwise use desktop selections
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
    
    // Show results list wrapper
    let resultsListWrapper = document.getElementById('results-list-wrapper');
    resultsListWrapper.classList.remove('hide');
    // Build query params to include multiple accessibility filters
    const params = new URLSearchParams();
    if (search) params.append('q', search);
    access.forEach(feature => params.append('accessibility', feature));
    let businesses = [];
    fetch(`/business/ajax/search-businesses/?${params.toString()}`)
    .then(response => response.json())
    .then(data => {
        businesses = data.businesses || [];
        // Store the latest results globally for toggling markers
        window.filteredBusinesses = businesses;
        // Render results list
        renderResultsList(businesses);
    });
}