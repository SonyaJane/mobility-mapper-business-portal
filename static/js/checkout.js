// Using Stripe Elements (PaymentIntent) for one-off payments

// get Stripe public key, price ID and server-created client_secret from template
const stripePublicKey = JSON.parse(document.getElementById('id_stripe_public_key').textContent);
const clientSecret = JSON.parse(document.getElementById('id_client_secret').textContent);
const paymentIntentId = JSON.parse(document.getElementById('id_payment_intent').textContent);

// Get error div for displaying errors
const errorDiv = document.getElementById('card-errors');

// Initialise Stripe
stripe = Stripe(stripePublicKey);
elements = stripe.elements();

// Create a card Element style
const style = {
    base: {
        iconColor: '#5f2c16',
        color: '#000',
        fontWeight: '500',
        fontFamily: 'Open Sans, sans-serif',
        fontSize: '16px',
        fontSmoothing: 'antialiased',
        ':-webkit-autofill': {
            color: '#fce883',
        },
        '::placeholder': {
            color: '#5f2c16',
        },
    },
    invalid: {
        iconColor: '#FFC7EE',
        color: '#FFC7EE',
    }
};

// Create card Element without the postal / ZIP code input
card = elements.create('card', {style: style, hidePostalCode: true});
// mount the card Element
card.mount('#card-element');

// Handle realtime validation errors on the card element
card.addEventListener('change', event => {
    if (event.error) {
        const html = `
            <span class="icon" role="alert">
                <i class="bi bi-x"></i>
            </span>
            <span>${event.error.message}</span>
        `;
        errorDiv.innerHTML = html;
    }
});

// Handle form submission

// Get form elements
const form = document.getElementById('payment-form');
const submitButton = document.getElementById('submit-button');
const loadingOverlay = document.getElementById('loading-overlay');

// Guard to prevent duplicate submits when a session is being created
let checkoutInProgress = false;

form.addEventListener('submit', async e => {
    e.preventDefault(); // Prevent default form submission

    // Prevent duplicate submits when a session is being created
    if (checkoutInProgress) return;
    checkoutInProgress = true;

    // Disable card element so user cannot change input
    card.update({ 'disabled': true}); 

    // Disable submit button
    submitButton.disabled = true;
    submitButton.classList.add('disabled');
    submitButton.setAttribute('aria-disabled', 'true');

    // Show loading overlay with spinner
    loadingOverlay.classList.remove('d-none');

    // Get selected membership tier input (tier id not used in this flow)
    const selectedTierInput = document.querySelector('input[name="membership_tier"]');
    // Get purchase type (membership or verification)
    const purchaseInput = document.querySelector('input[name="purchase"]');
    const purchase = purchaseInput ? purchaseInput.value : 'membership';

    // Get server-provided client_secret
    const initPaymentIntentId = paymentIntentId;

    const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
            card: card,
            billing_details: {
                name: document.querySelector('input[name="full_name"]').value,
                email: document.querySelector('input[name="email"]').value
            }
        }
    });

    // if there is an error put the error message in the error div
    if (result.error) {
        let html = `
            <span class="icon" role="alert">
            <i class="bi bi-x"></i>
            </span>
            <span>${result.error.message}</span>`;
        errorDiv.innerHTML = html;

        // Re-enable card element and submit button so user can try again
        card.update({ 'disabled': false });
        submitButton.removeAttribute('aria-disabled');
        submitButton.disabled = false;
        submitButton.classList.remove('disabled');            
        checkoutInProgress = false;
        const existingSpinner = document.getElementById('submit-button-spinner');
        if (existingSpinner) existingSpinner.style.display = 'none';
        if (loadingOverlay && loadingOverlay.classList) {
            loadingOverlay.classList.add('d-none');
            loadingOverlay.setAttribute('aria-hidden', 'true');
        }
    console.error('Payment failed', result.error);
    } else {
        // payment succeeded
        if (result.paymentIntent.status === 'succeeded') {
            form.submit();
        }
        // redirect to success page. We use paymentIntent id
        // as the reference so payment_success can show purchase details or poll.
        window.location.href = `/checkout/payment-success/?payment_intent_id=${encodeURIComponent(initPaymentIntentId || (result.paymentIntent && result.paymentIntent.id) || '')}`;
    }
});