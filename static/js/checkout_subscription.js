// Subscription-specific UI logic: tier & frequency selection, live amount update

// Helper to update summary amount and warning based on selections
function updateAmount() {
    const tierInputEl = document.querySelector('input[name="tier"]');
    const freqInputEl = document.querySelector('input[name="interval"]');
    const summaryAmtEl = document.getElementById('summary-amount');
    const warningStrong = document.getElementById('charge-warning')?.querySelector('strong');
    if (!(tierInputEl && freqInputEl && summaryAmtEl && warningStrong)) return;
    const selectedCard = document.querySelector(`.pricing-tier-card[data-tier-code="${tierInputEl.value}"]`);
    if (!selectedCard) return;
    const monthPrice = selectedCard.dataset.tierMonth;
    const yearPrice = selectedCard.dataset.tierYear;
    const selectedFreq = freqInputEl.value;
    const suffix = selectedFreq === 'yearly' ? 'year' : 'month';
    const rawAmount = selectedFreq === 'yearly' ? yearPrice : monthPrice;
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

    // Frequency toggles
    const freqBtn = document.getElementById('change-frequency-btn');
    const freqOptions = document.getElementById('checkout-frequency-options');
    const freqInput = document.querySelector('input[name="interval"]');
    const summaryFreq = document.getElementById('summary-frequency-display');
    if (freqBtn && freqOptions && freqInput && summaryFreq) {
        freqBtn.addEventListener('click', () => {
            freqOptions.classList.toggle('d-none');
        });
        freqOptions.querySelectorAll('.freq-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                freqInput.value = btn.dataset.freqValue;
                summaryFreq.textContent = btn.textContent;
                freqOptions.querySelectorAll('.freq-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                freqOptions.classList.add('d-none');
                updateAmount();
            });
        });
    }

    // Initial amount update
    updateAmount();
}

document.addEventListener('DOMContentLoaded', initSubscriptionUI);
