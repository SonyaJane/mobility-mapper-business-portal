/**
 * edit_business.js
 *
 * Handles dynamic interactivity for the Edit Business page:
 * - Initialises Choices.js for accessibility features and categories dropdowns.
 * - Enables auto-resizing for textareas.
 * - Initialises the opening hours widget.
 *
 * All logic is executed after DOMContentLoaded to ensure elements are present.
 */

import { initChoices, initAutoResize, initOpeningHours } from './form_helpers.js';

document.addEventListener('DOMContentLoaded', () => {
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

  // Auto-resize textareas
  initAutoResize('textarea.auto-resize');

  // Opening hours widget
  initOpeningHours('#opening-hours-table', '#id_opening_hours');
});
