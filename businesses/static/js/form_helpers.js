/**
 * form_helpers.js
 *
 * Utility functions for both register and edit business forms:
 * - Initialises Choices.js dropdowns for select fields.
 * - Toggles the "Other" category input based on selection.
 * - Enables auto-resizing for textareas.
 * - Initialises and manages the opening hours widget, including period copying and JSON serialisation.
 */

/**
 * Initialises Choices.js on the given select element.
 */
export function initChoices(selector, options) {
  const select = document.querySelector(selector);
  if (select && window.Choices) {
    new Choices(select, options);
  }
}

/**
 * Toggles the visibility of the "Other" category input field
 * based on whether the "__other__" option is selected in the categories dropdown.
 */
export function initOtherCategoryToggle(selectSelector, inputSelector) {
  const catSelect = document.querySelector(selectSelector);
  const otherField = document.querySelector(inputSelector);
  if (!catSelect || !otherField) return;
  function toggleOther() {
    const values = Array.from(catSelect.selectedOptions).map(o => o.value);
    otherField.style.display = values.includes('__other__') ? 'block' : 'none';
  }
  catSelect.addEventListener('change', toggleOther);
  toggleOther();
}

/**
 * Enables auto-resizing for all textareas matching the selector.
 */
export function initAutoResize(textareaSelector) {
  document.querySelectorAll(textareaSelector).forEach(textarea => {
    function resize() {
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    }
    textarea.addEventListener('input', resize);
    resize();
  });
}

/**
 * Initialises the opening hours widget:
 * - Allows adding/removing periods for each day.
 * - Supports copying periods to the next day.
 * - Serializes the opening hours as JSON into a hidden field on form submit.
 */
export function initOpeningHours(tableSelector, hiddenFieldSelector) {
  const openingHoursField = document.querySelector(hiddenFieldSelector);
  const table = document.querySelector(tableSelector);
  if (!openingHoursField || !table) return;

  let initial = {};
  try { initial = openingHoursField.value ? JSON.parse(openingHoursField.value) : {}; } catch {}

  function addPeriod(container, open = '', close = '') {
    const div = document.createElement('div');
    div.className = 'input-group mb-1 period-row';
    div.innerHTML = `
      <input type="time" class="form-control open-time" value="${open}" aria-label="Opening time">
      <span class="input-group-text">to</span>
      <input type="time" class="form-control close-time" value="${close}" aria-label="Closing time">
      <button type="button" class="btn btn-sm btn-outline-danger remove-period-btn" title="Remove">&times;</button>
    `;
    div.querySelector('.remove-period-btn').onclick = () => div.remove();
    container.appendChild(div);
  }

  const rows = Array.from(table.querySelectorAll('tbody tr'));
  rows.forEach((row, idx) => {
    const day = row.dataset.day;
    const container = row.querySelector('.periods-container');
    // Initialise with existing periods list (array of {start, end})
    const initialPeriods = Array.isArray(initial[day]) ? initial[day] : [];
    if (initialPeriods.length) {
      initialPeriods.forEach(p => addPeriod(container, p.start, p.end));
    } else {
      addPeriod(container);
    }

    row.querySelector('.add-period-btn').onclick = () => addPeriod(container);

    const copyBtn = row.querySelector('.copy-down-btn');
    if (copyBtn) copyBtn.onclick = () => {
      if (idx < rows.length - 1) {
        const next = rows[idx+1];
        const nextContainer = next.querySelector('.periods-container');
        nextContainer.innerHTML = '';
        container.querySelectorAll('.period-row').forEach(div => {
          const open = div.querySelector('.open-time').value;
          const close = div.querySelector('.close-time').value;
          if (open && close) addPeriod(nextContainer, open, close);
        });
        const nextCb = next.querySelector('.closed-checkbox');
        nextCb.checked = closedCb.checked; nextCb.dispatchEvent(new Event('change'));
      }
    };
  });

  table.closest('form').addEventListener('submit', () => {
    const data = {};
    rows.forEach(row => {
      const day = row.dataset.day;
      const periods = [];
      row.querySelectorAll('.period-row').forEach(div => {
        const open = div.querySelector('.open-time').value;
        const close = div.querySelector('.close-time').value;
        if (open && close) periods.push({ start: open, end: close });
      });
      data[day] = periods;
    });
    openingHoursField.value = JSON.stringify(data);
  });
}
