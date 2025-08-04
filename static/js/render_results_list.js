import renderBusinessAccordion from './render_business_accordion.js';
import toggleBusinessAccordion from './toggle_business_accordion.js';

export default function renderResultsList(businesses) {
    const list = document.getElementById('results-list');
    list.innerHTML = '';
    // Show results-container div
    const resultsContainer = document.getElementById('results-container');
    const searchInput = document.getElementById('business-search');
    if (businesses.length > 0) {
        if (resultsContainer) {
            resultsContainer.classList.add('results-visible');
            resultsContainer.classList.remove('hide');
        }
        // create list items for each returned business
        businesses.forEach((biz, idx) => {
            const li = document.createElement('li');
            // Tag list item with the business ID and coordinates for popup lookup
            li.setAttribute('data-id', biz.id);
            if (biz.location) {
                li.setAttribute('data-lat', biz.location.lat);
                li.setAttribute('data-lng', biz.location.lng);
            }
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
            // Create additional information in initially hidden accordion panel
            const infoPanel = document.createElement('div');
            infoPanel.className = 'accordion-collapse collapse';
            infoPanel.classList.add('hide');
            infoPanel.innerHTML = renderBusinessAccordion(biz);
            li.appendChild(infoPanel);
            // Get the arrow icon element
            const arrowIcon = li.querySelector('.toggle-arrow');
            // Listen for click to toggle accordion
            li.addEventListener('click', function(e) {
                e.stopPropagation();
                toggleBusinessAccordion(li, infoPanel, arrowIcon, biz);
            });
            list.appendChild(li);
        });
    } else { // No businesses found
        if (resultsContainer) {
            if (searchInput && searchInput.value.trim().length > 0) {
                // Only show no results found if search input has text
                resultsContainer.classList.add('results-visible');
                resultsContainer.classList.remove('hide'); 
                const noResults = document.createElement('li');
                noResults.className = 'list-group-item text-center text-muted';
                noResults.textContent = 'No results found.';
                list.appendChild(noResults);
            } else {
                resultsContainer.classList.remove('results-visible');
                resultsContainer.classList.add('hide');
            }
        }
    }
}