import { initChoices, initOtherCategoryToggle, initAutoResize, initOpeningHours } from './form_helpers.js';

document.addEventListener('DOMContentLoaded', () => {
  // Initialize shared form helpers
  initChoices('#id_accessibility_features', {
    removeItemButton: true,
    shouldSort: false,
    placeholder: true,
    placeholderValue: 'Select accessibility features'
  });

  initOtherCategoryToggle('#id_categories', '#other-category-field');

  initAutoResize('textarea.auto-resize');

  initOpeningHours('#opening-hours-table', '#id_opening_hours');
});