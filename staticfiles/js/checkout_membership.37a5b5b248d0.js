/**
 * checkout_membership.js
 *
 * Handles membership-specific UI logic for the checkout page:
 * - Updates the displayed amount and warning when a membership tier is selected.
 * - Manages tier selection interactions and redirects to the correct checkout URL.
 * - Highlights the currently selected membership tier.
 * 
 * All logic is executed after DOMContentLoaded to ensure elements are present.
 */

/**
 * Updates the displayed membership amount and warning message
 * based on the currently selected membership tier.
 */
function updateAmount() {
    const selectedTierInput = document.querySelector('input[name="membership_tier"]');
    const summaryAmtEl = document.getElementById('summary-amount');
    const warningStrong = document.getElementById('charge-warning')?.querySelector('strong');
    if (!(selectedTierInput && summaryAmtEl && warningStrong)) return;
    // Prefer matching by data-tier-id (FK) but fall back to data-tier-code if present
    let selectedCard = document.querySelector(`.membership-tier-card[data-tier-id="${selectedTierInput.value}"]`);
    if (!selectedCard) selectedCard = document.querySelector(`.membership-tier-card[data-tier-code="${selectedTierInput.value}"]`);
    if (!selectedCard) return;
    const rawAmount = selectedCard.dataset.tierPrice;
    const amount = parseFloat(rawAmount).toFixed(2);
    // Display annual price
    summaryAmtEl.textContent = `£${amount} for one year`;
    warningStrong.textContent = `£${amount}`;
}

/**
 * Initializes membership tier selection UI:
 * - Handles showing/hiding tier options.
 * - Handles tier card selection and redirects to the correct checkout URL.
 * - Highlights the currently selected tier.
 * - Updates the displayed amount on load.
 */
function initMembershipUI() {
    // Tier toggles
    const changeBtn = document.getElementById('change-tier-btn');
    const tierOptions = document.getElementById('checkout-tier-options');
    const selectedTierHidden = document.querySelector('input[name="membership_tier"]');
    const summaryDisplay = document.getElementById('summary-tier-display');
    // Require the canonical hidden `membership_tier` input when initialising.
    if (changeBtn && tierOptions && selectedTierHidden && summaryDisplay) {
        changeBtn.addEventListener('click', () => {
            tierOptions.style.display = tierOptions.style.display === 'none' ? 'flex' : 'none';
        });
        const cards = tierOptions.querySelectorAll('.membership-tier-card');
        cards.forEach(card => {
            card.addEventListener('click', () => {
                // Redirect to the checkout page with the membership_tier as a query param
                // so the server will re-render the page and create a PaymentIntent for that tier.
                const url = new URL(window.location.href);
                url.searchParams.set('membership_tier', card.dataset.tierId || card.dataset.tierCode || '');
                url.searchParams.set('purchase_type', 'membership');
                window.location.href = url.toString();
            });
        });
        // Highlight default
        cards.forEach(card => {
            // highlight by matching membership_tier FK if available, otherwise fall back to tierCode
            // Prefer the FK `membership_tier` value.
            const currentSelected = selectedTierHidden && selectedTierHidden.value || '';
            if (card.dataset.tierId === currentSelected || card.dataset.tierCode === currentSelected) {
                card.classList.add('border-primary', 'shadow');
            }
        });
    }

    // Initial amount update
    updateAmount();
}

// Initialise membership UI logic after DOM is loaded
document.addEventListener('DOMContentLoaded', initMembershipUI);
