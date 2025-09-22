/**
 * edit_profile.js
 *
 * Handles dynamic interactivity for the Edit Profile page:
 * - Shows or hides the "Other" mobility device field based on checkbox selection.
 * - Toggles county field visibility based on selected country.
 * 
 * All logic is executed after DOMContentLoaded to ensure elements are present.
 */
document.addEventListener('DOMContentLoaded', () => {
    const devicesField = document.getElementById('mobility-devices-field');
    const otherField = document.getElementById('mobility-other-field');

    function updateOtherField() {
        /**
         * Shows or hides the "Other" mobility device field
         * depending on whether the "Other" checkbox is checked.
         */
        if (!devicesField || !otherField) return;
        const otherCheckbox = devicesField.querySelector('input[type="checkbox"][value="other"]');
        const otherInput = otherField.querySelector('input[name="mobility_devices_other"]');
        if (otherCheckbox && otherCheckbox.checked) {
            otherField.style.display = 'block';
        } else {
            otherField.style.display = 'none';
        }
    }

    if (devicesField) {
        devicesField.addEventListener('change', updateOtherField);
        updateOtherField();
    }

    const countryContainer = document.getElementById('country-field');
    const countyContainer = document.getElementById('county-field');
    
    function updateCountyField() {
        // Toggles county visibility based on country selection
        if (!countryContainer || !countyContainer) return;
        const select = countryContainer.querySelector('select[name="country"]');
        if (select.value === 'Other') {
            countyContainer.style.display = 'none';
            const countySelect = countyContainer.querySelector('select[name="county"]');
            if (countySelect) countySelect.value = '';
        } else {
            countyContainer.style.display = 'block';
        }
    }

    const select = countryContainer.querySelector('select[name="country"]');
    
    if (select) {
        select.addEventListener('change', updateCountyField);
        updateCountyField();
    }
    
    function updateDevicesVisibility() {
        // Toggles mobility devices based on wheeler choice
        if (!devicesField) return;
        const isWheelerChecked = document.querySelector('input[name="is_wheeler"]:checked')?.value === 'True';
        if (isWheelerChecked) {
            devicesField.style.display = 'block';
            updateOtherField();
        } else {
            devicesField.style.display = 'none';
            otherField.style.display = 'none';
            devicesField.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        }
    }

    document.querySelectorAll('input[name="is_wheeler"]').forEach(radio => {
        radio.addEventListener('change', updateDevicesVisibility);
    });

    updateDevicesVisibility();
    
    // Show/hide other device text input when 'Other' checkbox changes
    function updateOtherVisibility() {
        // Find the checkbox whose label text is "Other"
        const otherCheckbox = Array.from(devicesField.querySelectorAll('input[type="checkbox"]'))
        .find(cb => cb.parentElement.textContent.trim().toLowerCase() === 'other');
        if (otherCheckbox && otherCheckbox.checked) {
            otherField.style.display = 'block';
        } else {
            otherField.style.display = 'none';
        }
    }

    // Delegate listener to devicesField container
    devicesField.addEventListener('change', updateOtherVisibility);
    updateOtherVisibility();
});