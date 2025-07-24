// Initialize Select2 for categories and accessibility features fields
$(document).ready(function() {
  $('#id_categories').select2({
    placeholder: 'Select business categories',
    width: '100%',
    allowClear: true
  });
  $('#id_accessibility_features').select2({
    placeholder: 'Select accessibility features',
    width: '100%',
    allowClear: true
  });
});
