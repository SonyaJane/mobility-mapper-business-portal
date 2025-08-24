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