import load_map from './load_map.js';

document.addEventListener('DOMContentLoaded', function() {
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
    const mapContainer = document.getElementById('map');

    // Businesses will be loaded via AJAX
    let businesses = [];
    // Initial data from server for random display
    let initialBusinesses = [];
    try {
        const dataScript = document.getElementById('business-data');
        if (dataScript && dataScript.textContent) {
            initialBusinesses = JSON.parse(dataScript.textContent);
        }
    } catch (e) { initialBusinesses = []; }

    // Load map
    load_map('map');
    
    // Render businesses on map
    function renderMarkers(filtered) {
        // Remove old markers (MapLibre)
        if (MAP.markers.length) {
        MAP.markers.forEach(m => m.remove());
        }
        MAP.markers = [];
        if (!MAP.map || !filtered) return;
        filtered.forEach((biz, idx) => {

        if (biz.location) {
            if (typeof maplibregl === 'undefined') {
            console.error('MapLibre GL JS is not loaded. Markers cannot be rendered.');
            return;
            }
            const el = document.createElement('div');
            el.className = 'map-marker';
            el.style.background = '#007bff';
            el.style.width = '24px';
            el.style.height = '24px';
            el.style.borderRadius = '50%';
            el.style.border = '2px solid white';
            el.style.boxShadow = '0 0 4px rgba(0,0,0,0.3)';
            const marker = new maplibregl.Marker(el)
            .setLngLat([biz.location.lng, biz.location.lat])
            .setPopup(new maplibregl.Popup().setHTML(`<strong>${biz.business_name}</strong><br>${biz.address}`))
            .addTo(MAP.map);
            MAP.markers.push(marker);
        }
        });
    }

    // Render results list
    function renderResults(filtered) {
    const list = document.getElementById('results-list');
    list.innerHTML = '';
    // Toggle mobile filters visibility
    const mobileFilters = document.getElementById('mobile-filters');
    const resultsWrapper = document.getElementById('results-list-wrapper');
    const searchInput = document.getElementById('business-search');
    if (filtered.length > 0) {
        if (mobileFilters) mobileFilters.style.display = '';
        if (resultsWrapper) {
            resultsWrapper.classList.add('results-visible');
            resultsWrapper.style.display = '';
        }
        filtered.forEach((biz, idx) => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            let categories = biz.categories && biz.categories.length ? biz.categories.join(', ') : '';
            let address = biz.address ? `<div>${biz.address}</div>` : '';
            let logo = biz.logo ? `<img src="${biz.logo}" alt="${biz.business_name} Logo" class="business-logo-img me-2">` : '';
            let verified = (biz.is_wheeler_verified === true || biz.is_wheeler_verified === 'true' || biz.is_wheeler_verified === 1 || biz.is_wheeler_verified === '1') ? `<div class="mt-2"><span class="text-success fw-bold">✅ Verified by Wheelers</span></div>` : '';
            li.innerHTML = `
                <div class="mb-1 d-flex justify-content-between w-100">
                    <div class="d-flex align-items-center flex-shrink-1">
                        ${logo ? `${logo}` : ``}
                        <h5 class="mb-0 business">${biz.business_name}</h5>
                    </div>
                    <i class="bi bi-chevron-down fs-6 toggle-arrow" aria-label="Expand business details"></i>
                </div>
                ${categories ? `<div class="mb-1 category">${categories}</div>` : ''}
                ${address}
                ${verified}
            `;
            li.style.cursor = 'pointer';
            // Accordion info panel
            const infoPanel = document.createElement('div');
            infoPanel.className = 'accordion-collapse collapse';
            infoPanel.style.display = 'none';
            infoPanel.innerHTML = renderBusinessAccordion(biz);
            li.appendChild(infoPanel);
            // Get the arrow icon element
            const arrowIcon = li.querySelector('.toggle-arrow');
            li.addEventListener('click', function(e) {
                e.stopPropagation();
                // Center the map on the business marker and zoom in
                if (biz.location && MAP.map) {
                    MAP.map.flyTo({ center: [biz.location.lng, biz.location.lat], zoom: 16 });
                }
                const allResults = document.querySelectorAll('#results-list > li');
                if (infoPanel.classList.contains('show')) {
                    infoPanel.classList.remove('show');
                    infoPanel.style.display = 'none';
                    if (arrowIcon) {
                        arrowIcon.classList.remove('bi-chevron-up');
                        arrowIcon.classList.add('bi-chevron-down');
                    }
                    // Show all results again and remove highlight
                    allResults.forEach(result => {
                        result.style.display = '';
                        result.classList.remove('single-visible');
                    });
                } else {
                    // Close any other open panels and reset arrows
                    const openPanels = document.querySelectorAll('.accordion-collapse.show');
                    openPanels.forEach(panel => {
                        panel.classList.remove('show');
                        panel.style.display = 'none';
                    });
                    const allArrows = document.querySelectorAll('.toggle-arrow');
                    allArrows.forEach(icon => {
                        icon.classList.remove('bi-chevron-up');
                        icon.classList.add('bi-chevron-down');
                    });
                    infoPanel.classList.add('show');
                    infoPanel.style.display = 'block';
                    if (arrowIcon) {
                        arrowIcon.classList.remove('bi-chevron-down');
                        arrowIcon.classList.add('bi-chevron-up');
                    }
                    // Hide all other results except this one, and add highlight
                    allResults.forEach(result => {
                        result.classList.remove('single-visible');
                        if (result !== li) {
                            result.style.display = 'none';
                        } else {
                            result.classList.add('single-visible');
                        }
                    });
                }
            });
            list.appendChild(li);
        });
    } else {
        if (mobileFilters) mobileFilters.style.display = '';
        if (resultsWrapper) {
            if (searchInput && searchInput.value.trim().length > 0) {
                resultsWrapper.classList.add('results-visible');
                resultsWrapper.style.display = '';
                // Only show 'No results found' if user has entered search text
                const noResults = document.createElement('li');
                noResults.className = 'list-group-item text-center text-muted';
                noResults.textContent = 'No results found.';
                list.appendChild(noResults);
            } else {
                resultsWrapper.classList.remove('results-visible');
                resultsWrapper.style.display = 'none';
            }
        }
    }

    // Renders additional biz info in accordion
    function renderBusinessAccordion(biz) {
        let accessibility = '';
        if (biz.accessibility_features && biz.accessibility_features.length) {
            accessibility = biz.accessibility_features.map(f => `<span class='badge accessibility-badge'>${f}</span>`).join(' ');
        }
        let website = biz.website ? `<a href=\"${biz.website}\" target=\"_blank\"><i class=\"bi bi-globe fs-5 me-2 text-primary\"></i>${biz.website}</a>` : '';
        let facebook = biz.facebook_url ? `<a href=\"${biz.facebook_url}\" target=\"_blank\" class=\"me-2\"><i class=\"bi bi-facebook text-primary\"></i></a>` : '';
        let instagram = biz.instagram_url ? `<a href=\"${biz.instagram_url}\" target=\"_blank\" class=\"me-2\"><i class=\"bi bi-instagram fs-5 me-2 text-danger\"></i></a>` : '';
        let x_twitter = biz.x_twitter_url ? `<a href=\"${biz.x_twitter_url}\" target=\"_blank\" class=\"me-2\"><i class=\"bi bi-twitter-x text-dark\"></i></a>` : '';
        let public_email = biz.public_email ? `<a href=\"mailto:${biz.public_email}\"><i class=\"bi bi-envelope fs-5 me-2 text-warning\"></i>${biz.public_email}</a>` : '';
        let phone = biz.public_phone ? `<i class='bi bi-telephone fs-5 me-2 text-danger'></i>${biz.public_phone}` : '';
        let description = biz.description ? `<i class='bi bi-card-text fs-5 me-2 text-info'></i>${biz.description}` : '';
        let services = biz.services_offered ? `<i class='bi bi-briefcase fs-5 me-2 text-primary'></i>${biz.services_offered}` : '';
        let offers = biz.special_offers ? `<i class='bi bi-tag fs-5 me-2 text-success'></i>${biz.special_offers}` : '';
        let opening_hours = biz.opening_hours ? renderOpeningHoursTable(biz.opening_hours) : '';        
        return `
            <div class=\"accordion-body mt-2 mb-1\">
                ${accessibility ? `<div class=\"mb-1\">${accessibility}</div>` : ''}
                ${website ? `<div class=\"mb-1\">${website}</div>` : ''}
                ${(facebook || instagram || x_twitter) ? `<div class=\"mb-1 d-flex flex-row align-items-center\"><i class='bi bi-share fs-5 me-2 text-success'></i>${facebook}${instagram}${x_twitter}</div>` : ''}
                ${public_email ? `<div class=\"mb-1\">${public_email}</div>` : ''}
                ${phone ? `<div class=\"mb-1\">${phone}</div>` : ''}
                ${description ? `<div class=\"mb-1\">${description}</div>` : ''}
                ${services ? `<div class=\"mb-1\">${services}</div>` : ''}
                ${offers ? `<div class=\"mb-1\">${offers}</div>` : ''}
                ${opening_hours}
            </div>
        `;
    }
    }

    function renderOpeningHoursTable(opening_hours) {
        if (!opening_hours) return '';
        let oh;
        try {
            oh = typeof opening_hours === 'string' ? JSON.parse(opening_hours) : opening_hours;
        } catch (e) {
            return '';
        }
        let html = `
            <div class="my-2"><strong>Opening Hours:</strong></div>
            <div class="table-responsive">
                <table class="table table-bordered table-sm w-auto mb-0" id="opening-hours-table-dashboard">
                    <tbody>
        `;
        Object.entries(oh).forEach(([day, info]) => {
            html += `<tr>
                <td class="px-2"><strong>${day}</strong></td>
                <td class="px-2">`;
            if (info.closed) {
                html += `<span class="text-muted">Closed</span>`;
            } else if (info.periods && info.periods.length) {
                html += info.periods.map((p, idx) =>
                    `<span>${p.open} - ${p.close}</span>${idx < info.periods.length - 1 ? '<br>' : ''}`
                ).join('');
            } else {
                html += `<span class="text-muted">No hours set</span>`;
            }
            html += `</td></tr>`;
        });
        html += `
                    </tbody>
                </table>
            </div>
        `;
        return html;
    }

    // Side panel for business info
    function filterBusinesses() {
        const search = document.getElementById('business-search').value;
        // Use mobile panel selects if visible, otherwise desktop
        let catId, access;
        const mobileFilters = document.getElementById('mobile-filters');
        if (mobileFilters && mobileFilters.style.display !== 'none') {
            const catSelect = document.getElementById('category-select-mobile-panel');
            catId = catSelect.value;
            // If the value is empty or matches the label, treat as 'all'
            if (!catId || catSelect.options[catSelect.selectedIndex].text === 'Category' || catSelect.options[catSelect.selectedIndex].text === 'All Categories') {
                catId = '';
            }
            const accessSelect = document.getElementById('accessibility-select-mobile-panel');
            access = accessSelect.value;
            if (!access || accessSelect.options[accessSelect.selectedIndex].text === 'Accessibility') {
                access = '';
            }
        } else {
            catId = document.getElementById('category-select').value;
            access = document.getElementById('accessibility-select').value;
        }
        if (!search && !catId && !access) {
            // No search/filter: show only the map, clear results
            renderMarkers([]);
            renderResults([]);
            return;
        }
        fetch(`/business/ajax/search-businesses/?q=${encodeURIComponent(search)}&category=${encodeURIComponent(catId)}&accessibility=${encodeURIComponent(access)}`)
        .then(response => response.json())
        .then(data => {
            businesses = data.businesses || [];
            // Render markers and results
            renderMarkers(businesses);
            renderResults(businesses);
        });
    }

    document.getElementById('business-search').addEventListener('input', filterBusinesses);
    document.getElementById('category-select').addEventListener('change', function() { filterBusinesses(); });
    document.getElementById('accessibility-select').addEventListener('change', function() { filterBusinesses(); });
    // Add listeners for mobile panel filter selects
    const catMobilePanel = document.getElementById('category-select-mobile-panel');
    const accessMobilePanel = document.getElementById('accessibility-select-mobile-panel');
    if (catMobilePanel) {
        catMobilePanel.addEventListener('change', function() { filterBusinesses(); });
    }
    if (accessMobilePanel) {
        accessMobilePanel.addEventListener('change', function() { filterBusinesses(); });
    }
    filterBusinesses();
    
    // Sync all category and accessibility filter selects
    function syncSelects(selectIds) {
    selectIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
        el.addEventListener('change', function() {
            selectIds.forEach(otherId => {
            if (otherId !== id) {
                const otherEl = document.getElementById(otherId);
                if (otherEl) otherEl.value = el.value;
            }
            });
            // Optionally trigger your filtering logic here
            if (typeof window.filterBusinesses === 'function') {
            window.filterBusinesses();
            }
        });
        }
    });
    }
    
  syncSelects(['category-select', 'category-select-mobile', 'category-select-mobile-panel']);
  syncSelects(['accessibility-select', 'accessibility-select-mobile', 'accessibility-select-mobile-panel']);

});
