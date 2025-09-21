/**
 * filter_businesses.js
 *
 * Handles filtering and displaying businesses on the Accessible Business Search page:
 * - Fetches businesses from the server based on search input, accessibility filters, and map bounds.
 * - Randomizes results on desktop when no filters are applied.
 * - Updates the results list and map markers in real time.
 * - Shows a loading spinner while fetching results.
 * - Handles stale/outdated AJAX responses to avoid race conditions.
 * - Stores the latest filtered businesses globally for use in other UI components.
 *
 * All logic is executed when filterBusinesses() is called (typically on input or filter change).
 */

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

// Token to track most recent request and ignore outdated responses
let lastRequestToken = 0;

export default function filterBusinesses() {
    // Increment token for this request
    const requestToken = ++lastRequestToken;

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
    
    // Show loading indicator in results list
    const list = document.getElementById('results-list');
    if (list) {
        list.innerHTML = '';
        const spinner = document.createElement('div');
        spinner.id = 'search-spinner';
        spinner.className = 'd-flex flex-row align-items-center justify-content-center my-3';
        spinner.innerHTML = `
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="m-2">Searching...</div>`;
        list.appendChild(spinner);
    }
    
    // Fetch businesses based on search, accessibility filters, and map bounds
    fetch(`/business/ajax/search-businesses/?${params.toString()}`)
    .then(response => {
        // If this is not the latest request, bail out
        if (requestToken !== lastRequestToken) throw new Error('stale');
        const spinnerEl = document.getElementById('search-spinner');
        if (spinnerEl) spinnerEl.remove();
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Ignore outdated responses
        if (requestToken !== lastRequestToken) return;
        const spinnerEl2 = document.getElementById('search-spinner');
        if (spinnerEl2) spinnerEl2.remove();
        businesses = data.businesses || [];
        // Client-side bounds filter: only keep businesses within current map viewport
        if (window.MAP && window.MAP.map && businesses.length > 0) {
            const bounds = window.MAP.map.getBounds();
            const sw = bounds.getSouthWest();
            const ne = bounds.getNorthEast();
            businesses = businesses.filter(b => {
                const loc = b.location;
                if (!loc) return false;
                return loc.lat >= sw.lat && loc.lat <= ne.lat && loc.lng >= sw.lng && loc.lng <= ne.lng;
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
        if (err.message === 'stale') return;
        // Remove loading indicator on error
        const spinnerEl3 = document.getElementById('search-spinner');
        if (spinnerEl3) spinnerEl3.remove();
        // Clear results list and markers on error
        renderResultsList([]);
        if (window.MAP && window.MAP.map) {
            window.MAP.map.resize();
            renderMarkers([]);
        }
    });
}