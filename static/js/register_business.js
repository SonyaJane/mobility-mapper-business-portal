import updatePrices from './update_prices.js';
import updateBillingActive from './update_billing_active.js';

document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.pricing-tier-card');
    const hiddenInput = document.getElementById('selected-pricing-tier');
    const billingRadios = document.querySelectorAll('input[name="billing_frequency"]');

    const featureSelect = document.getElementById('id_accessibility_features');
    if (featureSelect && window.Choices) {
      new Choices(featureSelect, {
        removeItemButton: true,
        shouldSort: false,
        placeholder: true,
        placeholderValue: 'Select accessibility features'
      });
    }

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
        const defaultCard = document.querySelector(`.pricing-tier-card[data-tier-id="${defaultTierId}"]`);
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

    billingRadios.forEach(radio => {
        radio.addEventListener('change', function() {
        updatePrices();
        updateBillingActive();
        });
        radio.addEventListener('click', function() {
        updatePrices();
        updateBillingActive();
        });
    });

    // Also update on click of the label (for accessibility)
    document.querySelectorAll('#billing-frequency-group label')
        .forEach(label => {
            label.addEventListener('click', () => {
            setTimeout(function() {
                updatePrices();
                updateBillingActive();
            }, 10); // Wait for radio to update
            });
        });

    // Initial update
    updatePrices();
    updateBillingActive();

    const catSelect = document.getElementById('id_categories');
        const otherField = document.getElementById('other-category-field');
        function toggleOther() {
            const values = Array.from(catSelect.selectedOptions).map(o => o.value);
            otherField.style.display = values.includes('__other__') ? 'block' : 'none';
        }
        catSelect.addEventListener('change', toggleOther);
        toggleOther();

    // Auto-resize for textareas
    document.querySelectorAll('textarea.auto-resize').forEach(function(textarea) {
      function resize() {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
      }
      textarea.addEventListener('input', resize);
      resize();
    });

    // Opening hours widget logic (multi-period)
    const openingHoursField = document.getElementById('id_opening_hours');
    const table = document.getElementById('opening-hours-table');
    let initial = {};
    try {
      if (openingHoursField.value) {
        initial = JSON.parse(openingHoursField.value);
      }
    } catch (e) {}

    function addPeriod(container, open = '', close = '') {
      const periodDiv = document.createElement('div');
      periodDiv.className = 'input-group mb-1 period-row';
      periodDiv.innerHTML = `
        <input type="time" class="form-control open-time" value="${open}">
        <span class="input-group-text">to</span>
        <input type="time" class="form-control close-time" value="${close}">
        <button type="button" class="btn btn-sm btn-outline-danger remove-period-btn" title="Remove">&times;</button>
      `;
      periodDiv.querySelector('.remove-period-btn').onclick = function() {
        periodDiv.remove();
      };
      container.appendChild(periodDiv);
    }

    const rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.forEach((row, idx) => {
      const day = row.dataset.day;
      const container = row.querySelector('.periods-container');
      // Populate from initial data or add one empty period
      if (initial[day] && !initial[day].closed && Array.isArray(initial[day].periods)) {
        initial[day].periods.forEach(period => {
          addPeriod(container, period.open, period.close);
        });
      } else {
        addPeriod(container);
      }
      // Add period button
      row.querySelector('.add-period-btn').onclick = function() {
        addPeriod(container);
      };
      // Closed checkbox logic
      const closedCb = row.querySelector('.closed-checkbox');
      function togglePeriods() {
        container.style.display = closedCb.checked ? 'none' : '';
        row.querySelector('.add-period-btn').style.display = closedCb.checked ? 'none' : '';
      }
      closedCb.addEventListener('change', togglePeriods);
      togglePeriods();
      if (initial[day] && initial[day].closed) {
        closedCb.checked = true;
        togglePeriods();
      }
      // Copy to next day button logic
      const copyBtn = row.querySelector('.copy-down-btn');
      if (copyBtn) {
        copyBtn.onclick = function() {
          if (idx < rows.length - 1) {
            const nextRow = rows[idx + 1];
            const nextContainer = nextRow.querySelector('.periods-container');
            nextContainer.innerHTML = '';
            container.querySelectorAll('.period-row').forEach(periodDiv => {
              const open = periodDiv.querySelector('.open-time').value;
              const close = periodDiv.querySelector('.close-time').value;
              if (open && close) {
                addPeriod(nextContainer, open, close);
              }
            });
            // Copy closed state
            const nextClosed = nextRow.querySelector('.closed-checkbox');
            nextClosed.checked = closedCb.checked;
            nextClosed.dispatchEvent(new Event('change'));
          }
        };
      }
    });

    // Serialize table to hidden field before submit
    document.querySelector('.business-registration-form').addEventListener('submit', function() {
      const data = {};
      rows.forEach(row => {
        const day = row.dataset.day;
        const closed = row.querySelector('.closed-checkbox').checked;
        if (closed) {
          data[day] = { closed: true };
        } else {
          const periods = [];
          row.querySelectorAll('.periods-container .period-row').forEach(periodDiv => {
            const open = periodDiv.querySelector('.open-time').value;
            const close = periodDiv.querySelector('.close-time').value;
            if (open && close) {
              periods.push({ open, close });
            }
          });
          data[day] = { closed: false, periods };
        }
      });
      openingHoursField.value = JSON.stringify(data);
    });


});