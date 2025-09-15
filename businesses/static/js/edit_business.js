import { initChoices, initOtherCategoryToggle, initAutoResize, initOpeningHours } from './form_helpers.js';

document.addEventListener('DOMContentLoaded', () => {
  // Initialize shared form helpers
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

  // Toggle other category field
  initOtherCategoryToggle('#id_categories', '#other-category-field');

  // Auto-resize textareas
  initAutoResize('textarea.auto-resize');

  // Opening hours widget
  initOpeningHours('#opening-hours-table', '#id_opening_hours');
});
