import load_map from './load_map.js';

document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('route-map');

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
    load_map('route-map');
    
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
        filtered.forEach((biz, idx) => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        let categories = biz.categories && biz.categories.length ? biz.categories.join(', ') : '';
        let address = biz.address ? `<div class="mb-2">${biz.address}</div>` : '';
        let logo = biz.logo ? `<img src="${biz.logo}" alt="${biz.business_name} Logo" class="business-logo-img">` : '';
        let verified = (biz.is_wheeler_verified === true || biz.is_wheeler_verified === 'true' || biz.is_wheeler_verified === 1 || biz.is_wheeler_verified === '1') ? `<span class="text-success fw-bold">✅ Verified by Wheelers</span><br>` : '';
        li.innerHTML = `            
            ${logo 
                ? `<div class="mb-2 d-flex align-items-center">${logo}<h4 class="ms-2">${biz.business_name}</h4></div>` 
                : `<h4 class="mb-2">${biz.business_name}</h4>`
            }
            ${categories ? `<div class="mb-2">${categories}</div>` : ''}
            ${address}
            <div class="mb-2">${verified}</div>
        `;
        li.style.cursor = 'pointer';
        // Accordion info panel
        const infoPanel = document.createElement('div');
        infoPanel.className = 'accordion-collapse collapse';
        infoPanel.style.display = 'none';
        infoPanel.innerHTML = renderBusinessAccordion(biz);
        li.appendChild(infoPanel);
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
                // Show all results again
                allResults.forEach(result => {
                    result.style.display = '';
                });
            } else {
                // Close any other open panels
                const openPanels = document.querySelectorAll('.accordion-collapse.show');
                openPanels.forEach(panel => {
                    panel.classList.remove('show');
                    panel.style.display = 'none';
                });
                infoPanel.classList.add('show');
                infoPanel.style.display = 'block';
                // Hide all other results except this one
                allResults.forEach(result => {
                    if (result !== li) {
                        result.style.display = 'none';
                    }
                });
            }
        });
        list.appendChild(li);

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
            <div class=\"accordion-body mb-3\">
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
        });
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
            <div class="mt-3 mb-2"><strong>Opening Hours:</strong></div>
            <div class="table-responsive">
                <table class="table table-bordered table-sm w-auto" id="opening-hours-table-dashboard">
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
        const catId = document.getElementById('category-select').value;
        const access = document.getElementById('accessibility-select').value;
        if (!search && !catId && !access) {
            // Show a random sample of businesses if no search/filter
            let sample = initialBusinesses.slice();
            // Shuffle and pick up to 8
            for (let i = sample.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [sample[i], sample[j]] = [sample[j], sample[i]];
            }
            sample = sample.slice(0, 8);
            renderMarkers(sample);
            renderResults(sample);
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
    document.getElementById('category-select').addEventListener('change', filterBusinesses);
    document.getElementById('accessibility-select').addEventListener('change', filterBusinesses);
    // Show random businesses on initial load
    filterBusinesses();

});
