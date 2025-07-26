import load_map from './load_map.js';

document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('route-map');

    // Businesses will be loaded via AJAX
    let businesses = [];

    // Load map
    load_map('route-map');
    
    // Render businesses on map
    function renderMarkers(filtered) {
        // Remove old markers (MapLibre)
        if (MAP.markers.length) {
        MAP.markers.forEach(m => m.remove());
        }
        MAP.markers = [];
        console.log('map:', MAP.map, 'filtered:', filtered);
        if (!MAP.map || !filtered) return;
        filtered.forEach((biz, idx) => {
        console.log('Rendering marker for business:', biz);
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
        let accessibility = '';
        if (biz.accessibility_features && biz.accessibility_features.length) {
          accessibility = biz.accessibility_features.map(f => `<span class="badge accessibility-badge">${f}</span>`).join(' ');
        }
        let verified = (biz.is_wheeler_verified === true || biz.is_wheeler_verified === 'true' || biz.is_wheeler_verified === 1 || biz.is_wheeler_verified === '1') ? `<span class="text-success fw-bold">✅ Verified by Wheelers</span><br>` : '';
        li.innerHTML = `            
            <strong>${biz.business_name}</strong><br>
            ${categories}<br>
            ${biz.address}<br>
            ${verified}
            `;
        li.style.cursor = 'pointer';
        li.addEventListener('click', function() {
            if (MAP.markers[idx] && MAP.markers[idx].getPopup()) {
                MAP.markers[idx].togglePopup();
            }
            // Center the map on the business marker and zoom in
            if (biz.location && MAP.map) {
                MAP.map.flyTo({ center: [biz.location.lng, biz.location.lat], zoom: 16 });
            }
            showBusinessPanel(biz);
        });
        list.appendChild(li);
        });
    }

    // Side panel for business info
    function showBusinessPanel(biz) {
        const panel = document.getElementById('business-details-panel');
        if (!panel) return;
        let categories = biz.categories && biz.categories.length ? biz.categories.join(', ') : '';
        let phone = biz.public_phone ? `<i class='bi bi-telephone me-1'></i>${biz.public_phone}` : '';
        let public_email = biz.public_email ? `<br><i class='bi bi-envelope me-1'></i><a href="mailto:${biz.public_email}">${biz.public_email}</a>` : '';
        let website = biz.website ? `<i class='bi bi-globe me-1'></i><a href="${biz.website}" target="_blank">${biz.website}</a>` : '';
        let address = biz.address ? `<i class='bi bi-geo-alt me-1'></i>${biz.address}` : '';
        let opening_hours = biz.opening_hours ? `<i class='bi bi-clock me-1'></i>${biz.opening_hours}` : '';
        let offers = biz.special_offers ? `<br><i class='bi bi-tag me-1'></i>${biz.special_offers}` : '';
        let services = biz.services_offered ? `<br><i class='bi bi-briefcase me-1'></i>${biz.services_offered}` : '';
        let description = biz.description ? `<br><i class='bi bi-info-circle me-1'></i>${biz.description}` : '';
        let logo = biz.logo ? `<img src="${biz.logo}" alt="${biz.business_name} Logo" class="business-logo-img">` : '';
        let verified = (biz.is_wheeler_verified === true || biz.is_wheeler_verified === 'true' || biz.is_wheeler_verified === 1 || biz.is_wheeler_verified === '1') ? `<span class="text-success fw-bold">✅ Verified by Wheelers</span><br>` : '';
        let accessibility = '';
        if (biz.accessibility_features && biz.accessibility_features.length) {
            accessibility = `` + biz.accessibility_features.map(f => `<span class="badge accessibility-badge">${f}</span>`).join(' ');
        }
        panel.innerHTML = `
            <div class="d-flex justify-content-end w-100">
                <button class="btn btn-light business-panel-close mt-2 me-2" id="close-business-panel">&times;</button>
            </div>
            <div class="card border-0">
                <div class="card-header bg-white border-0 pb-0">
                    ${logo ? `
                        <div class="text-center mb-2 business-logo-container">${logo}</div>
                    ` : ''}
                    <h4 class="card-title mb-0 text-center">${biz.business_name}</h4>
                </div>
                <div class="card-body pt-2">                    
                    ${categories ? `<div class="mb-2 text-center">${categories}</div>` : ''}
                    <div class="container-fluid px-0">
                        ${address ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-geo-alt'></i></div>
                            <div class="col ps-2">${biz.address}</div>
                        </div>` : ''}
                        ${opening_hours ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-clock'></i></div>
                            <div class="col ps-2">${biz.opening_hours}</div>
                        </div>` : ''}
                        ${website ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-globe'></i></div>
                            <div class="col ps-2"><a href="${biz.website}" target="_blank">${biz.website}</a></div>
                        </div>` : ''}
                        ${public_email ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-envelope'></i></div>
                            <div class="col ps-2"><a href="mailto:${biz.public_email}">${biz.public_email}</a></div>
                        </div>` : ''}
                        ${phone ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-telephone'></i></div>
                            <div class="col ps-2">${biz.public_phone}</div>
                        </div>` : ''}                        
                        ${description ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-info-circle'></i></div>
                            <div class="col ps-2">${biz.description}</div>
                        </div>` : ''}
                        ${services ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-briefcase'></i></div>
                            <div class="col ps-2">${biz.services_offered}</div>
                        </div>` : ''}
                        ${offers ? `
                        <div class="row mb-1">
                            <div class="col-auto d-flex align-items-center justify-content-end icon-col"><i class='bi bi-tag'></i></div>
                            <div class="col ps-2">${biz.special_offers}</div>
                        </div>` : ''}
                        ${accessibility ? `
                        <div class="mb-1">
                            <p class="fw-bold mb-1 mt-2">Accessibility Features</p>
                            ${biz.accessibility_features.map(f => `<span class='badge accessibility-badge'>${f}</span>`).join(' ')}
                            ${verified ? `<div class="my-1">${verified}</div>` : ''}
                        </div>` : ''}
                    </div>
                </div>
            </div>
        `;
        panel.style.display = 'block';
        // Overlay for outside click
        let overlay = document.getElementById('business-panel-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'business-panel-overlay';
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'block';
        overlay.onclick = function() {
            panel.style.display = 'none';
            overlay.style.display = 'none';
        };
        document.getElementById('close-business-panel').onclick = function() {
            panel.style.display = 'none';
            overlay.style.display = 'none';
        };
        // Swipe/drag to close (basic)
        let startX = null;
        panel.onmousedown = function(e) { startX = e.clientX; };
        panel.onmouseup = function(e) {
            if (startX !== null && e.clientX - startX > 120) {
                panel.style.display = 'none';
                overlay.style.display = 'none';
            }
            startX = null;
        };
        // Touch support
        panel.ontouchstart = function(e) { if (e.touches.length === 1) startX = e.touches[0].clientX; };
        panel.ontouchend = function(e) {
            if (startX !== null && e.changedTouches[0].clientX - startX > 80) {
                panel.style.display = 'none';
                overlay.style.display = 'none';
            }
            startX = null;
        };
    }
    function filterBusinesses() {
        const search = document.getElementById('business-search').value;
        const catId = document.getElementById('category-select').value;
        const access = document.getElementById('accessibility-select').value;
        fetch(`/map/ajax/search-businesses/?q=${encodeURIComponent(search)}&category=${encodeURIComponent(catId)}&accessibility=${encodeURIComponent(access)}`)
        .then(response => response.json())
        .then(data => {
            businesses = data.businesses || [];
            console.log('Filtered businesses:', businesses);
            // Render markers and results
            renderMarkers(businesses);
            renderResults(businesses);
        });
    }

    document.getElementById('business-search').addEventListener('input', filterBusinesses);
    document.getElementById('category-select').addEventListener('change', filterBusinesses);
    document.getElementById('accessibility-select').addEventListener('change', filterBusinesses);

});
