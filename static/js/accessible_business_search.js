import renderMarkers from './render_markers.js';
import load_map from './load_map.js';
import filterBusinesses from './filter_businesses.js';
import syncSelects from './sync_selects.js';

document.addEventListener('DOMContentLoaded', function() {

    // Load map
    const mapContainer = document.getElementById('map');
    load_map(mapContainer);

    // Listen for search input 
    document.getElementById('business-search').addEventListener('input', filterBusinesses);
    
    const desktopSelect = document.getElementById('accessibility-select');
    if (desktopSelect) {
    new Choices(desktopSelect, {
        removeItemButton: true,
        shouldSort: false,
        placeholder: true,
        placeholderValue: 'Click to filter by accessibility Features'
    }).passedElement.element.addEventListener('change', filterBusinesses);
    }

    const mobileSelect = document.getElementById('accessibility-select-mobile-panel');
    if (mobileSelect) {
    new Choices(mobileSelect, {
        removeItemButton: true,
        shouldSort: false,
        placeholder: true,
        placeholderValue: 'Tap to filter by accessibility features',
        position: 'bottom'
    }).passedElement.element.addEventListener('change', filterBusinesses);
    }

    // Sync selects across desktop and mobile views    
    syncSelects(['accessibility-select', 'accessibility-select-mobile', 'accessibility-select-mobile-panel']);

    // Clear search box when X button is clicked
    const clearSearchBtn = document.getElementById('clear-search');
    const businessSearchInput = document.getElementById('business-search');
    if (clearSearchBtn && businessSearchInput) {
        clearSearchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Clear search input
            businessSearchInput.value = '';
            // hide results div
            const resultsWrapper = document.getElementById('results-list-wrapper');
            if (resultsWrapper) {
                resultsWrapper.classList.add('hide');
            }            
            businessSearchInput.focus();
        });
    }

    // Arrow toggle for results list
    const resultsListWrapper = document.getElementById('results-list-wrapper');
    const resultsToggle = document.getElementById('results-toggle');
    let resultsHidden = false;

    // Wire up list view and map view buttons
    const mapViewBtn = document.getElementById('show-map-view-btn');
    const listViewBtn = document.getElementById('show-list-view-btn');
    
    mapViewBtn.addEventListener('click', () => {
        // Show markers and hide list
        if (window.filteredBusinesses) renderMarkers(window.filteredBusinesses);
        resultsListWrapper.classList.add('hide');
        // show list view button on map                
        listViewBtn.classList.remove('hide');
    });

    listViewBtn.addEventListener('click', () => {
        // show results list
        resultsListWrapper.classList.remove('hide');
        // hide listview button
        listViewBtn.classList.add('hide');
    });


    // Hide/show results arrow for md and up
    if (resultsToggle) {
        resultsToggle.addEventListener('click', function() {
            resultsHidden = !resultsHidden;
            if (resultsHidden) {
                resultsListWrapper.classList.add('hide-results');
                resultsToggle.setAttribute('aria-label', 'Show results');
                resultsToggle.innerHTML = '<i class="bi bi-arrow-right-circle fs-3"></i>';
            } else {
                resultsListWrapper.classList.remove('hide-results');
                resultsToggle.setAttribute('aria-label', 'Hide results');
                resultsToggle.innerHTML = '<i class="bi bi-arrow-left-circle fs-3"></i>';
            }
        });
    }

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
