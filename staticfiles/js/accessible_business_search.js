import renderMarkers from './render_markers.js';
import load_map from './load_map.js';
import filterBusinesses from './filter_businesses.js';

document.addEventListener('DOMContentLoaded', function() {

    // Load map
    const mapContainer = document.getElementById('map');
    load_map(mapContainer);

    // Listen for search input 
    // On desktop: real-time filtering; on mobile: wait for Search button
    const searchInput = document.getElementById('business-search');
    if (window.matchMedia('(min-width: 768px)').matches) {
        searchInput.addEventListener('input', filterBusinesses);
    } else {
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => filterBusinesses());
        }
    }

    // listen for map panning or zoom changes to trigger filtering only on desktop
    if (window.MAP && window.MAP.map && window.matchMedia('(min-width: 768px)').matches) {
        // Only re-filter once the user finishes dragging (panning) or zooming on larger screens
        window.MAP.map.on('dragend', filterBusinesses);
        window.MAP.map.on('zoomend', filterBusinesses);
    }

    const accessibilitySelect = document.getElementById('accessibility-select');
    let accessibilityChoices;
    if (accessibilitySelect) {
        accessibilityChoices = new Choices(accessibilitySelect, {
            removeItemButton: true,
            shouldSort: false,
            placeholder: true,
            placeholderValue: 'Filter by accessibility Features'
        });
        // rerun filter when selection changes
        accessibilityChoices.passedElement.element.addEventListener('change', filterBusinesses);
        // Show/hide the clear-all button based on selection count
        const clearAccessBtn = document.getElementById('clear-accessibility');
        if (clearAccessBtn) {
            accessibilityChoices.passedElement.element.addEventListener('change', () => {
                const hasSelected = accessibilityChoices.getValue(true).length > 0;
                clearAccessBtn.classList.remove('hide', !hasSelected);
            });
        }
    }

    // Initial random results on md+ when no input yet
    if (window.matchMedia('(min-width: 768px)').matches) {
        filterBusinesses();
    }
    // Clear all accessibility selections when clear button is clicked
    const clearAccessBtn = document.getElementById('clear-accessibility');
    if (clearAccessBtn && accessibilityChoices) {
        clearAccessBtn.addEventListener('click', () => {
            accessibilityChoices.removeActiveItems();
            filterBusinesses();
            // hide clear button after clearing selections
            clearAccessBtn.classList.add('hide');
        });
    }

    // Clear search box when X button is clicked
    const clearSearchBtn = document.getElementById('clear-search');
    const businessSearchInput = document.getElementById('business-search');
    if (clearSearchBtn && businessSearchInput) {
        clearSearchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Clear search input
            businessSearchInput.value = '';
            // hide results div
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.add('hide');
            // remove markers from map
            renderMarkers([]);            
            businessSearchInput.focus();
            }
    });
    }

    // Mobile view toggle

    // Wire up list view and map view buttons
    const mapViewBtn = document.getElementById('show-map-view-btn');
    const listViewBtn = document.getElementById('show-list-view-btn');
    const resultsContainer = document.getElementById('results-container');
    
    mapViewBtn.addEventListener('click', () => {
        // Show markers and hide list
        if (window.filteredBusinesses) renderMarkers(window.filteredBusinesses);
        resultsContainer.classList.add('hide');
        // show list view button on map                
        listViewBtn.classList.remove('hide');
    });

    listViewBtn.addEventListener('click', () => {
        // show results list
        resultsContainer.classList.remove('hide');
        // hide listview button
        listViewBtn.classList.add('hide');
    });

    // Show detailed info overlay when clicking 'Show more info' in popup
    document.addEventListener('click', function(e) {
        if (e.target.matches('.show-more-info')) {
            e.preventDefault();
            const id = e.target.getAttribute('data-id');
            const listItem = document.querySelector(`#results-list li[data-id="${id}"]`);
            const overlay = document.getElementById('info-overlay');
            const body = document.getElementById('info-overlay-body');
            if (listItem && overlay && body) {
                // Build overlay content: popup portion + accordion details
                // Clone list item and remove toggle arrow
                const clone = listItem.cloneNode(true);
                const arrowIcon = clone.querySelector('.toggle-arrow');
                if (arrowIcon) arrowIcon.remove();
                let content = clone.innerHTML;
                // Append accordion panel content
                const panel = listItem.querySelector('.accordion-collapse');
                if (panel) {
                    content += panel.innerHTML;
                }
                body.innerHTML = content;
                overlay.classList.remove('hide');
            }
        }
        // Close overlay
        if (e.target.matches('#info-overlay-close')) {
            const overlay = document.getElementById('info-overlay');
            if (overlay) overlay.classList.add('hide');
        }
    });
    
});
