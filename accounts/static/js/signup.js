/**
 * signup.js
 *
 * Handles dynamic interactivity for the Signup page:
 * - Provides live username availability feedback via AJAX.
 * - Shows or hides the mobility devices field based on wheeler selection.
 * - Shows or hides the "Other" mobility device text input based on checkbox selection.
 * 
 * All logic is executed after DOMContentLoaded to ensure elements are present.
 */
document.addEventListener('DOMContentLoaded', function() {

    /**
     * Shows live feedback if the entered username is available.
     * Sends an AJAX request to the server to validate the username.
     */
    // check the username input field exists on the page
    const usernameInput = document.querySelector('input[name="username"]');
    if (!usernameInput) return;
    // create a feedback element
    const feedback = document.createElement('div');
    feedback.classList.add('mt-1','small');
    usernameInput.parentNode.appendChild(feedback);
    let timer;
    usernameInput.addEventListener('input', function() {
        clearTimeout(timer);
        const val = this.value.trim();
        // Only allow letters, numbers, dots, and underscores
        if (!val) { feedback.textContent = ''; return; }
        if (!/^[\w.]+$/.test(val)) {
            feedback.textContent = 'Username can only contain letters, numbers, dots, or underscores.';
            feedback.classList.remove('text-success');
            feedback.classList.add('text-danger');
            return;
        }
        if (val.length < 5) {
            feedback.textContent = 'Username must be at least 5 characters long.';
            feedback.classList.remove('text-success');
            feedback.classList.add('text-danger');
            return;
        }
        timer = setTimeout(() => {
            fetch(validateUsernameUrl + "?username=" + encodeURIComponent(val))
                .then(r => r.json())
                .then(data => {
                    feedback.textContent = data.available ? 'Username is available.' : 'Username is already taken.';
                    feedback.classList.toggle('text-success', data.available);
                    feedback.classList.toggle('text-danger', !data.available);
                });
        }, 300);
    });

    // Show/hide mobility devices based on wheeler choice
    const yesWheeler = document.querySelector('input[name="is_wheeler"][value="True"]');
    const noWheeler = document.querySelector('input[name="is_wheeler"][value="False"]');
    const devicesField = document.getElementById('mobility-devices-field');
    const otherField = document.getElementById('mobility-other-field');
    function updateDevicesVisibility() {
        if (yesWheeler && yesWheeler.checked) {
            devicesField.style.display = 'block';
        } else {
            devicesField.style.display = 'none';
            otherField.style.display = 'none';
        }
    }
    if (yesWheeler && noWheeler) {
    yesWheeler.addEventListener('change', updateDevicesVisibility);
    noWheeler.addEventListener('change', updateDevicesVisibility);
    }
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
