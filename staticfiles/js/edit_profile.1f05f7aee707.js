document.addEventListener('DOMContentLoaded', function() {
    const devicesField = document.getElementById('mobility-devices-field');
    const otherField = document.getElementById('mobility-other-field');
    function updateOtherField() {
    if (!devicesField || !otherField) return;
    const otherCheckbox = devicesField.querySelector('input[type="checkbox"][value="other"]');
    const otherInput = otherField.querySelector('input[name="mobility_devices_other"]');
    if (otherCheckbox && otherCheckbox.checked) {
        otherField.style.display = 'block';
    } else {
        otherField.style.display = 'none';
        if (otherInput) otherInput.value = '';
    }
    }
    if (devicesField) {
    devicesField.addEventListener('change', updateOtherField);
    updateOtherField();
    }
    // Toggle county visibility based on country selection
    const countryContainer = document.getElementById('country-field');
    const countyContainer = document.getElementById('county-field');
    function updateCountyField() {
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
    // Toggle mobility devices based on wheeler choice
    function updateDevicesVisibility() {
        if (!devicesField) return;
        const isWheelerChecked = document.querySelector('input[name="is_wheeler"]:checked')?.value === 'True';
        if (isWheelerChecked) {
            devicesField.style.display = 'block';
            updateOtherField();
        } else {
            devicesField.style.display = 'none';
            otherField.style.display = 'none';
            devicesField.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            const otherInput = otherField.querySelector('input[name="mobility_devices_other"]');
            if (otherInput) otherInput.value = '';
        }
    }
    document.querySelectorAll('input[name="is_wheeler"]').forEach(radio => {
    radio.addEventListener('change', updateDevicesVisibility);
    });
    updateDevicesVisibility();
    // Show/hide other device text input when 'Other' checkbox changes
    function updateOtherVisibility() {
        const otherCheckbox = document.querySelector('#mobility-devices-field input[type="checkbox"][value="other"]');
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