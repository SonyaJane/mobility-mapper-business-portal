/**
 * wheeler_verification_form.js
 *
 * Handles client-side validation and interactivity for the Wheeler Verification Form:
 * - Validates required fields (selfie, mobility device, feature photos) before submission.
 * - Displays inline error messages above relevant sections and scrolls to the first error.
 * - Manages feature photo upload, preview, and removal for each accessibility feature.
 * - Syncs feature photo selection with the corresponding checkbox.
 * - Ensures a smooth user experience with dynamic UI updates.
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    // Clear existing errors and add inline errors per section
   
    // Client-side validation to preserve file inputs
    form.addEventListener('submit', e => {
      // Remove any existing inline error blocks
      document.querySelectorAll('.error-block').forEach(el => el.remove());
      const errors = [];
      // Selfie required
      const selfieInput = form.querySelector('input[name="selfie"]');
      if (!selfieInput || !selfieInput.files.length) {
        errors.push({ msg: 'Please upload a photo of yourself.', section: '#selfie-section' });
      }
      // Mobility device required
      if (!form.querySelector('input[name="mobility_device"]:checked')) {
        errors.push({ msg: 'Select the mobility device you are using.', section: '#mobility-device-section' });
      }
      // Feature photos required when feature checked
      document.querySelectorAll('.feature-photo-wrapper').forEach(wrapper => {
        const checkbox = wrapper.closest('tr').querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
          const input = wrapper.querySelector('.feature-photo-input');
          if (!input.files.length) {
            const featureName = wrapper.closest('tr').querySelector('label').innerText.trim();
            // Determine which section this feature belongs to
            const tBody = wrapper.closest('tbody');
            const sectionId = tBody.closest('div').id;
            errors.push({ msg: `A photo is required for feature ${featureName}.`, section: `#${sectionId}` });
          }
        }
      });
      if (errors.length) {
        e.preventDefault();
        // Insert error messages above each relevant section and scroll to first
        errors.forEach(err => {
          const sectionEl = document.querySelector(err.section);
          if (sectionEl) {
            const div = document.createElement('div');
            div.className = 'alert alert-danger error-block';
            div.textContent = err.msg;
            sectionEl.parentNode.insertBefore(div, sectionEl);
          }
        });
        const firstError = document.querySelector('.error-block');
        if (firstError) {
          // Scroll error to top of viewport, accounting for fixed header
          const header = document.querySelector('.header-container');
          const headerHeight = header ? header.offsetHeight : 0;
          const errorTop = firstError.getBoundingClientRect().top + window.pageYOffset;
          window.scrollTo({ top: errorTop - headerHeight, behavior: 'smooth' });
        }
      }
    });

    document.querySelectorAll('.feature-photo-wrapper').forEach(wrapper => {
      const btn = wrapper.querySelector('.feature-photo-btn');
      const input = wrapper.querySelector('.feature-photo-input');
      const status = wrapper.querySelector('.feature-photo-status');
      const preview = wrapper.querySelector('.feature-photo-preview');
      // Sync with the feature checkbox in the same row
      const checkbox = wrapper.closest('tr').querySelector('.form-check-input');
      const removeLink = wrapper.querySelector('.remove-photo');
      btn.addEventListener('click', () => input.click());
      input.addEventListener('change', () => {
        if (input.files.length) {
          // Tick the associated checkbox when a photo is chosen
          if (checkbox) checkbox.checked = true;
          const file = input.files[0];
          const url = URL.createObjectURL(file);
          preview.src = url;
          preview.classList.remove('d-none');
          btn.classList.add('d-none');
          status.classList.remove('d-none');
        }
      });
      removeLink.addEventListener('click', e => {
        e.preventDefault();
        input.value = '';
        preview.src = '#';
        preview.classList.add('d-none');
        status.classList.add('d-none');
        btn.classList.remove('d-none');
      });
    });
  });
