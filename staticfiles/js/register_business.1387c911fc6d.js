/**
 * register_business.js
 *
 * Handles dynamic interactivity for the Register Business page:
 * - Initialises Choices.js for accessibility features and categories dropdowns.
 * - Manages membership tier card selection and highlights the selected tier.
 * - Sets the hidden input value for the selected membership tier.
 * - Supports keyboard accessibility for card selection.
 * - Toggles the "Other" category field based on selection.
 * - Enables auto-resizing for textareas.
 * - Initialises the opening hours widget.
 *
 * All logic is executed after DOMContentLoaded to ensure elements are present.
 */

import { initChoices, initOtherCategoryToggle, initAutoResize, initOpeningHours } from './form_helpers.js';

document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.membership-tier-card');
    const hiddenInput = document.getElementById('selected-membership-tier');

    // Initialise shared form helpers
    initChoices('#id_accessibility_features', {
      removeItemButton: true,
      shouldSort: false,
      placeholder: true,
      placeholderValue: 'Select accessibility features'
    });
    // Enhance categories dropdown with Choices.js
    initChoices('#id_categories', {
      removeItemButton: true,
      shouldSort: false,
      placeholder: true,
      placeholderValue: 'Select business categories'
    });

    // Card selection logic
    cards.forEach(card => {
        card.addEventListener('click', function() {
        // Clear existing selection
        cards.forEach(c => c.classList.remove('border-primary', 'shadow'));
        // Highlight selected card
        card.classList.add('border-primary', 'shadow');
        // Set hidden input value to the selected tier ID
        hiddenInput.value = card.dataset.tierId;
        });

        // Set default tier if one is initially selected in Django
        const defaultTierId = hiddenInput.value;
        if (defaultTierId) {
        const defaultCard = document.querySelector(`.membership-tier-card[data-tier-id="${defaultTierId}"]`);
        if (defaultCard) {
            defaultCard.classList.add('border-primary', 'shadow');
        }
        }

        card.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            card.click();
        }
        });
    });
    
    initOtherCategoryToggle('#id_categories', '#other-category-field');

    initAutoResize('textarea.auto-resize');

    initOpeningHours('#opening-hours-table', '#id_opening_hours');

});