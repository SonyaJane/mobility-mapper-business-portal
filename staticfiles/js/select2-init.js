// Initialize Select2 for categories field
$(document).ready(function() {
  $('#id_categories').select2({
    placeholder: 'Select business categories',
    width: '100%',
    allowClear: true
  });
});
