/**
 * render_results_list.js
 *
 * Exports a function to render the list of businesses in the search results panel.
 * - Creates list items for each business, including logo, name, categories, address, and badges.
 * - Handles verified and verification-requested badges.
 * - Renders an accordion panel with detailed business info.
 * - Handles toggling of the accordion and prevents toggling when clicking the verification badge.
 * - Displays a "No results found" message if the list is empty.
 */

import renderBusinessAccordion from './render_business_accordion.js';
import toggleBusinessAccordion from './toggle_business_accordion.js';

export default function renderResultsList(businesses) {
    const list = document.getElementById('results-list');
    list.innerHTML = '';
    // Show results-container div
    const resultsContainer = document.getElementById('results-container');
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
            // Combine separate address fields into a single formatted block
            let addressParts = [];
            if (biz.street_address1) addressParts.push(biz.street_address1);
            if (biz.street_address2) addressParts.push(biz.street_address2);
            if (biz.town_or_city) addressParts.push(biz.town_or_city);
            if (biz.county) addressParts.push(biz.county);
            if (biz.postcode) addressParts.push(biz.postcode);
            let address = addressParts.length ? `<div class="mb-1">${addressParts.join(', ')}</div>` : '';
            let logo = biz.logo ? `<img src="${biz.logo}" alt="${biz.business_name} Logo" class="business-logo-img me-2">` : '';
            let verified = (biz.is_wheeler_verified === true || biz.is_wheeler_verified === 'true' || biz.is_wheeler_verified === 1 || biz.is_wheeler_verified === '1') ? `<div class="mt-2 px-2 py-1 btn-green-outline rounded d-inline-block"><span class="fw-bold"><i class="bi bi-check-circle-fill pe-2"></i>Verified by Wheelers</span></div>` : '';
            // Badge for businesses that have requested verification (only for verified wheelers)
            let requestedBadge = (typeof isVerifiedWheeler !== 'undefined' && isVerifiedWheeler && biz.wheeler_verification_requested) ?
                `<a href="/verification/${biz.id}/wheeler-verification-application/" 
                    class="badge badge-verify box-shadow text-body mt-2">
                        Verify the accessibility of this business and earn a £10 Amazon voucher
                </a>` : '';
            li.innerHTML = `
                <div class="mb-1 d-flex justify-content-between w-100">
                    <div class="d-flex align-items-center flex-shrink-1">
                        ${logo ? `${logo}` : ``}
                        <div>
                            <h5 class="mb-1 business">${biz.business_name}</h5>
                            ${categories ? `<div class="mb-0 category">${categories}</div>` : ''}
                        </div>
                    </div>
                    <i class="bi bi-chevron-down fs-6 toggle-arrow"></i>
                </div>                
                ${address}
                ${verified}
                ${requestedBadge}
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
            // Prevent toggling when clicking the verification request badge
            const badgeLink = li.querySelector('.badge.badge-verify');
            if (badgeLink) {
                badgeLink.addEventListener('click', function(e) {
                    e.stopPropagation();
                    // Allow link navigation without toggling accordion
                });
            }
            list.appendChild(li);
        });
    } else { // No businesses found
        if (resultsContainer) {
            // Always show the container and display a 'No results found' message
            resultsContainer.classList.add('results-visible');
            resultsContainer.classList.remove('hide');
            const noResults = document.createElement('li');
            noResults.className = 'list-group-item text-center text-muted';
            noResults.textContent = 'No results found.';
            list.appendChild(noResults);
        }
    }
}