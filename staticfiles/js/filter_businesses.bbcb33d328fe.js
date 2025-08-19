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
    // Include map viewport bounds if map is initialized
    if (window.MAP && window.MAP.map) {
        const bounds = window.MAP.map.getBounds();
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        params.append('min_lat', sw.lat);
        params.append('min_lng', sw.lng);
        params.append('max_lat', ne.lat);
        params.append('max_lng', ne.lng);
    }
    // Fetch businesses based on search, accessibility filters, and map bounds
    fetch(`/business/ajax/search-businesses/?${params.toString()}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        businesses = data.businesses || [];
        // Client-side bounds filter: only keep businesses within current map viewport
        if (window.MAP && window.MAP.map && businesses.length > 0) {
            const bounds = window.MAP.map.getBounds();
            const sw = bounds.getSouthWest();
            const ne = bounds.getNorthEast();
            businesses = businesses.filter(b => {
                const loc = b.location;
                if (!loc) return false;
                return loc.lat >= sw.lat && loc.lat <= ne.lat
                    && loc.lng >= sw.lng && loc.lng <= ne.lng;
            });
        }
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
    })
    .catch(err => {
        console.error('Search failed', err);
        // Clear results list and markers on error
        renderResultsList([]);
        if (window.MAP && window.MAP.map) {
            window.MAP.map.resize();
            renderMarkers([]);
        }
    });
}