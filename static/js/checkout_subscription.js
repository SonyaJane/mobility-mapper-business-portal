// Subscription-specific UI logic: tier selection, live amount update

// Subscription-specific UI logic: tier selection (tier_code), live amount update
function updateAmount() {
    const tierInputEl = document.querySelector('input[name="tier_code"]');
    const summaryAmtEl = document.getElementById('summary-amount');
    const warningStrong = document.getElementById('charge-warning')?.querySelector('strong');
    if (!(tierInputEl && summaryAmtEl && warningStrong)) return;
    const selectedCard = document.querySelector(`.pricing-tier-card[data-tier-code="${tierInputEl.value}"]`);
    if (!selectedCard) return;
    const rawAmount = selectedCard.dataset.tierPrice;
    const amount = parseFloat(rawAmount).toFixed(2);
    // Display annual price
    summaryAmtEl.textContent = `£${amount} for one year`;
    warningStrong.textContent = `£${amount}`;
}

// Subscription page interactions
function initSubscriptionUI() {
    // Tier toggles
    const changeBtn = document.getElementById('change-tier-btn');
    const tierOptions = document.getElementById('checkout-tier-options');
    const tierInput = document.querySelector('input[name="tier_code"]');
    const summaryDisplay = document.getElementById('summary-tier-display');
    if (changeBtn && tierOptions && tierInput && summaryDisplay) {
        changeBtn.addEventListener('click', () => {
            tierOptions.style.display = tierOptions.style.display === 'none' ? 'flex' : 'none';
        });
        const cards = tierOptions.querySelectorAll('.pricing-tier-card');
        cards.forEach(card => {
            card.addEventListener('click', () => {
                cards.forEach(c => c.classList.remove('border-primary', 'shadow'));
                card.classList.add('border-primary', 'shadow');
                tierInput.value = card.dataset.tierCode;
                // set hidden selected_tier FK value
                const selectedTierInput = document.querySelector('input[name="selected_tier"]');
                if (selectedTierInput) selectedTierInput.value = card.dataset.tierId;
                summaryDisplay.textContent = card.dataset.tierDisplay;
                tierOptions.style.display = 'none';
                updateAmount();
            });
        });
        // Highlight default
        cards.forEach(card => {
            if (card.dataset.tierCode === tierInput.value) {
                card.classList.add('border-primary', 'shadow');
            }
        });
    }

    // Initial amount update
    updateAmount();
}

document.addEventListener('DOMContentLoaded', initSubscriptionUI);
