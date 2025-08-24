// Retrieve Stripe keys from JSON script tags
const stripePublicKey = JSON.parse(document.getElementById('id_stripe_public_key').textContent);
const clientSecret = JSON.parse(document.getElementById('id_client_secret').textContent);

// Initialise Stripe
const stripe = Stripe(stripePublicKey);
const elements = stripe.elements();

// Stripe Element styling
const style = {
    base: {
        iconColor: '#432b20',
        color: '#000',
        fontWeight: '600',
        fontFamily: 'Open Sans, sans-serif',
        fontSize: '24px',
        fontSmoothing: 'antialiased',
        ':-webkit-autofill': { color: '#F7CE9DF0' },
        '::placeholder': { color: '#865640b9' }
    },
    invalid: { iconColor: '#FFC7EE', color: '#FFC7EE' }
};

// Create and mount the Card Element
const card = elements.create('card', { style });
card.mount('#card-element');

// Handle real-time validation errors
card.on('change', (e) => {
    const errorDiv = document.getElementById('card-errors');
    if (e.error) {
        errorDiv.innerHTML = `
            <span class="icon" role="alert">
                <i class="fas fa-times"></i>
            </span>
            <span>${e.error.message}</span>
        `;
    } else {
        errorDiv.textContent = '';
    }
});

// Form and UI elements
const form = document.getElementById('payment-form');
const submitButton = document.getElementById('submit-button');
const loadingOverlay = document.getElementById('loading-overlay');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    // Disable UI
    card.update({ disabled: true });
    submitButton.disabled = true;
    form.classList.add('d-none');
    loadingOverlay.classList.remove('d-none');

    // Gather data
    const saveCheckbox = document.getElementById('id-save-info');
    const saveInfo = saveCheckbox ? saveCheckbox.checked : false;
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    const body = new URLSearchParams({
        csrfmiddlewaretoken: csrfToken,
        client_secret: clientSecret,
        save_info: saveInfo
    });

    try {
        // Cache checkout data server-side
        const response = await fetch('/checkout/cache_checkout_data/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body.toString()
        });
        if (!response.ok) throw new Error('Network response error');

        // Confirm card payment
        const result = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: card,
                billing_details: {
                    name: form.full_name.value.trim(),
                    phone: form.phone_number.value.trim(),
                    email: form.email.value.trim(),
                    address: {
                        line1: form.street_address1.value.trim(),
                        line2: form.street_address2.value.trim(),
                        city: form.town_or_city.value.trim(),
                        state: form.county.value.trim(),
                        postal_code: form.postcode.value.trim(),
                    }
                }
            }
        });

        if (result.error) {
            const errorDiv = document.getElementById('card-errors');
            errorDiv.innerHTML = `
                <span class="icon" role="alert">
                    <i class="fas fa-times"></i>
                </span>
                <span>${result.error.message}</span>
            `;
            form.classList.remove('d-none');
            loadingOverlay.classList.add('d-none');
            card.update({ disabled: false });
            submitButton.disabled = false;
        } else if (result.paymentIntent && result.paymentIntent.status === 'succeeded') {
            // Optionally submit the form or redirect
            // form.submit();
        }
    } catch (error) {
        window.location.reload();
    }
});

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

    // Wire up Change Tier functionality
document.addEventListener('DOMContentLoaded', () => {
    const changeBtn = document.getElementById('change-tier-btn');
    const tierOptions = document.getElementById('checkout-tier-options');
    const tierInput = document.querySelector('input[name="tier"]');
    const summaryDisplay = document.getElementById('summary-tier-display');
    if (changeBtn && tierOptions && tierInput && summaryDisplay) {
        changeBtn.addEventListener('click', () => {
            tierOptions.style.display = tierOptions.style.display === 'none' ? 'flex' : 'none';
        });
        // Handle tier card clicks
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
        // Highlight default tier
        cards.forEach(card => {
            if (card.dataset.tierCode === tierInput.value) {
                card.classList.add('border-primary', 'shadow');
            }
        });
    }
    // Change Frequency functionality (separate from tier logic)
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
                // Highlight active freq
                freqOptions.querySelectorAll('.freq-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                freqOptions.classList.add('d-none');
                updateAmount();
            });
        });
    }
    // Initial update on page load
    updateAmount();
});