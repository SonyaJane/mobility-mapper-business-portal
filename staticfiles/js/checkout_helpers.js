// Checkout helpers - small reusable functions for the checkout flow

// handleFailure shows a friendly error message and re-enables the checkout UI
// Accepts an optional `card` Element if the caller wants to explicitly pass it.

// handleFailure shows a friendly error message and re-enables the checkout UI
export function handleFailure(message, card) {
    const errorDiv = document.getElementById('card-errors');
    const submitButton = document.getElementById('submit-button');
    const loadingOverlay = document.getElementById('loading-overlay');

    const html = `
        <span class="icon" role="alert">
            <i class="bi bi-x"></i>
        </span>
        <span>${message}</span>`;
    if (errorDiv) errorDiv.innerHTML = html;

    card.update({ disabled: false });
    
    submitButton.removeAttribute('aria-disabled');
    submitButton.disabled = false;
    submitButton.classList.remove('disabled');

    // Reset the global progress 
    window.checkoutInProgress = false;

    loadingOverlay.classList.add('d-none');

    // Move focus to the error container so screen readers announce the message
    // and the user is taken directly to the visible error.
    if (errorDiv) {
        // make the div programmatically focusable if it isn't already
        errorDiv.setAttribute('tabindex', '-1');
        errorDiv.focus();
        // smooth-scroll it into view for better UX
        if (typeof errorDiv.scrollIntoView === 'function') {
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
};
