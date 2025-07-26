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
            // Show modal with business info
            showBusinessModal(biz);
        });
        list.appendChild(li);
        });
    }

    // Modal for business info
    function showBusinessModal(biz) {
        let modal = document.getElementById('business-info-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'business-info-modal';
            modal.className = 'modal fade';
            modal.tabIndex = -1;
            modal.setAttribute('data-bs-backdrop', 'true');
            modal.setAttribute('data-bs-keyboard', 'true');
            modal.innerHTML = `
                <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                    <h5 class="modal-title"></h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body"></div>
                </div>
                </div>
            `;
            document.body.appendChild(modal);
            }
        
        // Fill modal content
        modal.querySelector('.modal-title').textContent = biz.business_name;
        let categories = biz.categories && biz.categories.length ? biz.categories.join(', ') : '';
        let accessibility = '';
        if (biz.accessibility_features && biz.accessibility_features.length) {
          accessibility = `<br><strong>Accessibility:</strong> ` + biz.accessibility_features.map(f => `<span class="badge accessibility-badge">${f}</span>`).join(' ');
        }
        let phone = biz.public_phone ? `<br><strong>Phone:</strong> ${biz.public_phone}` : '';
        let public_email = biz.public_email ? `<br><strong>Email:</strong> <a href="mailto:${biz.public_email}">${biz.public_email}</a>` : '';
        let website = biz.website ? `<br><strong>Website:</strong> <a href="${biz.website}" target="_blank">${biz.website}</a>` : '';
        let address = biz.address ? `<br><strong>Address:</strong> ${biz.address}` : '';
        let opening_hours = biz.opening_hours ? `<br><strong>Opening Hours:</strong> ${biz.opening_hours}` : '';
        let offers = biz.special_offers ? `<br><strong>Offers:</strong> ${biz.special_offers}` : '';
        let services = biz.services_offered ? `<br><strong>Services Offered:</strong> ${biz.services_offered}` : '';
        let description = biz.description ? `<br><strong>Description:</strong> ${biz.description}` : '';
        let logo = biz.logo ? `<br><img src="${biz.logo}" alt="${biz.business_name} Logo" style="max-width:100px;max-height:100px;">` : '';
        let verified = (biz.is_wheeler_verified === true || biz.is_wheeler_verified === 'true' || biz.is_wheeler_verified === 1 || biz.is_wheeler_verified === '1') ? `<span class="text-success fw-bold">✅ Verified by Wheelers</span><br>` : '';
        modal.querySelector('.modal-body').innerHTML = `
        ${logo}
        <strong>${biz.business_name}</strong><br>
        ${verified}
        ${categories}<br>
        ${address}
        ${accessibility}
        ${phone}
        ${public_email}
        ${website}
        ${opening_hours}
        ${offers}
        ${services}
        ${description}
        `;
        // Show modal
        let bsModal = bootstrap.Modal.getOrCreateInstance(modal);
        bsModal.show();
        // Allow closing modal by clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
            bsModal.hide();
            }
        });
    }

    // AJAX search businesses
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
