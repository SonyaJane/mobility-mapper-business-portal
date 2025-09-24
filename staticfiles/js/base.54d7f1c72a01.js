document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function() {
      form.querySelectorAll('[type="submit"]').forEach(function(btn) {
        btn.disabled = true;
        btn.innerHTML = 'please wait...';
      });
    });
  });
});