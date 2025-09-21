/**
 * accessible_business_search.js
 *
 * Handles all interactivity for the Accessible Business Search page:
 * - Loads and initializes the map.
 * - Filters businesses in real time or on button click (depending on device width).
 * - Integrates Choices.js for accessibility feature filtering.
 * - Handles map and list view toggling on mobile.
 * - Manages clear buttons for search and accessibility filters.
 * - Displays detailed info overlays for businesses.
 * 
 * All logic is executed after DOMContentLoaded to ensure elements are present.
 */

import renderMarkers from './render_markers.js';
import load_map from './load_map.js';
import filterBusinesses from './filter_businesses.js';

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Loads the map into the map container.
     */
    const mapContainer = document.getElementById('map');
    load_map(mapContainer);

    /**
     * Sets up search input filtering:
     * - On desktop, filters in real time as the user types.
     * - On mobile, filters when the Search button is clicked.
     */
    const searchInput = document.getElementById('business-search');
    if (window.matchMedia('(min-width: 768px)').matches) {
        searchInput.addEventListener('input', filterBusinesses);
    } else {
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => filterBusinesses());
        }
    }

    /**
     * Triggers filtering when the map is panned or zoomed (desktop only).
     */
    if (window.MAP && window.MAP.map && window.matchMedia('(min-width: 768px)').matches) {
        // Only re-filter once the user finishes dragging (panning) or zooming on larger screens
        window.MAP.map.on('dragend', () => {
                filterBusinesses();
            }
        );
        window.MAP.map.on('zoomend', () => {
            filterBusinesses();
        });
    }

    /**
     * Initializes Choices.js for accessibility feature filtering.
     * Shows/hides the clear-all button based on selection.
     */
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
                if (hasSelected) {
                    clearAccessBtn.classList.remove('hide');
                } else {
                    clearAccessBtn.classList.add('hide');
                }
            });
        }
    }

    /**
     * Shows random results on desktop when no input is present.
     */
    if (window.matchMedia('(min-width: 768px)').matches) {
        filterBusinesses();
    }

    /**
     * Clears all accessibility selections when the clear button is clicked.
     */
    const clearAccessBtn = document.getElementById('clear-accessibility');
    if (clearAccessBtn && accessibilityChoices) {
        clearAccessBtn.addEventListener('click', () => {
            accessibilityChoices.removeActiveItems();
            filterBusinesses();
            // hide clear button after clearing selections
            clearAccessBtn.classList.add('hide');
        });
    }

    /**
     * Clears the search box and refreshes the list/map when the X button is clicked.
     */
    const clearSearchBtn = document.getElementById('clear-search');
    const businessSearchInput = document.getElementById('business-search');
    if (clearSearchBtn && businessSearchInput) {
        clearSearchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Clear search input
            businessSearchInput.value = '';
            // Refresh list/map with empty search
            filterBusinesses();
            businessSearchInput.focus();
        });
    }

    /**
     * Handles mobile view toggling between map and list.
     */
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

    /**
     * Displays a detailed info overlay when 'Show more info' is clicked in a popup.
     * Closes the overlay when the close button is clicked.
     */
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
