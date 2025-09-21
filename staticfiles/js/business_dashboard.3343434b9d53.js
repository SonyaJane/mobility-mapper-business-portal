/**
 * business_dashboard.js
 *
 * Handles the map display on the Business Dashboard page:
 * - Loads business data from a JSON script tag.
 * - Initializes and displays the map for the business using load_map_business.
 * 
 * All logic is executed after DOMContentLoaded to ensure elements are present.
 */

import load_map_business from './load_map_business.js';

document.addEventListener("DOMContentLoaded", function() {
    const business = JSON.parse(document.getElementById('business-data').textContent);
    load_map_business("public-map", business);
});