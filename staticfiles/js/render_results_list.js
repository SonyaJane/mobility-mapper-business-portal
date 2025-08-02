import renderBusinessAccordion from './render_business_accordion.js';

export default function renderResults(filtered) {
    // Renders additional biz info in accordion

    updateBadges();
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
                        <div>
                            <h5 class="mb-1 business">${biz.business_name}</h5>
                            ${categories ? `<div class="mb-0 category">${categories}</div>` : ''}
                        </div>
                    </div>
                    <i class="bi bi-chevron-down fs-6 toggle-arrow" aria-label="Click to expand business details"></i>
                </div>                
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
}