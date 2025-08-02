import renderBusinessAccordion from './render_business_accordion.js';
import toggleBusinessAccordion from './toggle_business_accordion.js';

export default function renderResultsList(filtered) {
    // Renders additional biz info in accordion
    const list = document.getElementById('results-list');
    list.innerHTML = '';
    // Toggle mobile filter, and results visibility
    const mobileFilters = document.getElementById('mobile-filters');
    const resultsWrapper = document.getElementById('results-list-wrapper');
    const searchInput = document.getElementById('business-search');
    if (filtered.length > 0) {
        mobileFilters.classList.remove('hide');
        if (resultsWrapper) {
            resultsWrapper.classList.add('results-visible');
            resultsWrapper.classList.remove('hide');
        }
        // create list items for each returned business
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