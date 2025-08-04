import renderResultsList from './render_results_list.js';
import renderMarkers from './render_markers.js';

// Utility to shuffle an array
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

export default function filterBusinesses() {
    // Get the search input value
    const search = document.getElementById('business-search').value;
   
    // Get accessibility filter selections
    let access;
    access = Array.from(document.getElementById('accessibility-select').selectedOptions)
        .map(o => o.value)
        .filter(v => v);
    
    // Show results list container
    let resultsListWrapper = document.getElementById('results-container');
    resultsListWrapper.classList.remove('hide');

    // Build query params to include multiple accessibility filters
    // Create URLSearchParams object
    const params = new URLSearchParams(); 
    // Include search term if present
    if (search) params.append('q', search); 
    // Append each selected accessibility feature
    access.forEach(feature => params.append('accessibility', feature)); 

    let businesses = [];
    // Fetch businesses based on search and accessibility filters
    fetch(`/business/ajax/search-businesses/?${params.toString()}`)
    .then(response => response.json())
    .then(data => {
        businesses = data.businesses || [];
        // On md+ screens with no search or accessibility filters, randomise initial list
        const isDesktop = window.matchMedia('(min-width: 768px)').matches;
        if (!search && access.length === 0 && isDesktop) {
            businesses = shuffleArray(businesses);
        }
        // Store the latest results globally for toggling markers on mobile screens
        window.filteredBusinesses = businesses;
        // Render results list
        renderResultsList(businesses);
        // Resize the map after the list sidebar toggles to keep the centre consistent
        if (window.MAP && window.MAP.map) {
            window.MAP.map.resize();
        }
        // Render markers on the map for md+ screens
        if (isDesktop) {
            renderMarkers(businesses);
        }        
    });
}