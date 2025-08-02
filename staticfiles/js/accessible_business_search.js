import load_map from './load_map.js';
import filterBusinesses from './filter_businesses.js';
import updateBadges from './update_badges.js';
import syncSelects from './sync_selects.js';
import renderMarkers from './render_markers.js';

document.addEventListener('DOMContentLoaded', function() {

    // Load map
    const mapContainer = document.getElementById('map');
    load_map(mapContainer);

    // Listen for search input 
    document.getElementById('business-search').addEventListener('input', filterBusinesses);

    // Listen for accessibility filter select changes
    document.getElementById('accessibility-select').addEventListener('change', filterBusinesses);
    
    // Add listeners for mobile panel filter selects, update badges on change
    const accessMobilePanel = document.getElementById('accessibility-select-mobile-panel');
    if (accessMobilePanel) {
        accessMobilePanel.addEventListener('change', function() { updateBadges(); filterBusinesses(); });
    }

    // Sync selects across desktop and mobile views    
    syncSelects(['accessibility-select', 'accessibility-select-mobile', 'accessibility-select-mobile-panel']);


    // Clear search box when X button is clicked
    const clearSearchBtn = document.getElementById('clear-search');
    const businessSearchInput = document.getElementById('business-search');
    if (clearSearchBtn && businessSearchInput) {
        clearSearchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            businessSearchInput.value = '';
            if (typeof filterBusinesses === 'function') {
                filterBusinesses();
            }
            businessSearchInput.focus();
        });
    }
    // Store desktop selected filters
    let desktopFilters = [];
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

    
    // Initial badge render
    updateBadges();
    
    // Mobile badges
    const mobileSelect = document.getElementById('accessibility-select-mobile-panel');
    const mobileContainer = document.getElementById('accessibility-badges-mobile');
    if (mobileSelect && mobileContainer) {
        mobileContainer.innerHTML = '';
        Array.from(mobileSelect.selectedOptions).forEach(opt => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-secondary me-1 d-inline-flex align-items-center';
            badge.textContent = opt.value;
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn-close btn-close-white btn-sm ms-1';
            btn.setAttribute('aria-label', 'Remove');
            btn.addEventListener('click', e => {
                e.stopPropagation();
                opt.selected = false;
                updateBadges();
                filterBusinesses();
            });
            badge.appendChild(btn);
            mobileContainer.appendChild(badge);
        });
    }

    // Render desktop badges from desktopFilters array
    desktopFilters.forEach((val, idx) => {
        const badge = document.createElement('span');
        badge.className = 'badge bg-secondary me-1 d-inline-flex align-items-center';
        badge.textContent = val;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-close btn-close-white btn-sm ms-1';
        btn.setAttribute('aria-label', 'Remove');
        btn.addEventListener('click', e => {
            e.stopPropagation();
            desktopFilters.splice(idx, 1);
            updateBadges();
            filterBusinesses();
        });
        badge.appendChild(btn);
        container.appendChild(badge);
    });

});
