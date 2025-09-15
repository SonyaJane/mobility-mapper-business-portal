import load_map_business from './load_map_business.js';

document.addEventListener("DOMContentLoaded", function() {
    const business = JSON.parse(document.getElementById('business-data').textContent);
    load_map_business("public-map", business);
});