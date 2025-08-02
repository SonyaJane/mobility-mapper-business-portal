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
        placeholderValue: 'Filter by Accessibility Features'
    }).passedElement.element.addEventListener('change', filterBusinesses);
    }

    const mobileSelect = document.getElementById('accessibility-select-mobile-panel');
    if (mobileSelect) {
    new Choices(mobileSelect, {
        removeItemButton: true,
        shouldSort: false,
        placeholder: true,
        placeholderValue: 'Filter by Accessibility Features',
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
    
});
