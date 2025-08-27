// Subscription-specific UI logic: tier selection, live amount update

// Helper to update summary amount and warning based on selections
function updateAmount() {
    const tierInputEl = document.querySelector('input[name="tier"]');
    const summaryAmtEl = document.getElementById('summary-amount');
    const warningStrong = document.getElementById('charge-warning')?.querySelector('strong');
    if (!(tierInputEl && summaryAmtEl && warningStrong)) return;
    const selectedCard = document.querySelector(`.pricing-tier-card[data-tier-code="${tierInputEl.value}"]`);
    if (!selectedCard) return;
    const yearPrice = selectedCard.dataset.tierYear;
    const rawAmount = yearPrice
    const amount = parseFloat(rawAmount).toFixed(2);
    summaryAmtEl.textContent = `£${amount} / ${suffix}`;
    warningStrong.textContent = `£${amount} per ${suffix}`;
}

// Subscription page interactions
function initSubscriptionUI() {
    // Tier toggles
    const changeBtn = document.getElementById('change-tier-btn');
    const tierOptions = document.getElementById('checkout-tier-options');
    const tierInput = document.querySelector('input[name="tier"]');
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
