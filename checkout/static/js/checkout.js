import { handleFailure } from "./checkout_helpers.js";

// use a window-scoped guard so helpers running in a different module can reset it
window.checkoutInProgress = window.checkoutInProgress || false;
// Using Stripe Elements (PaymentIntent) for one-off payments

// get Stripe public key and server-created client_secret from template
const stripePublicKey = JSON.parse(document.getElementById('id_stripe_public_key').textContent);
const clientSecret = JSON.parse(document.getElementById('id_client_secret').textContent);
const paymentIntentId = JSON.parse(document.getElementById('id_payment_intent').textContent);
// Read business id from container data attribute
const businessId = document.querySelector('[data-business-id]')?.dataset?.businessId || '';

// Get error div for displaying errors
const errorDiv = document.getElementById('card-errors');

// Initialise Stripe
let stripe = Stripe(stripePublicKey);
let elements = stripe.elements();

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
let card = elements.create('card', {style: style, hidePostalCode: true});
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

form.addEventListener('submit', async e => {
    e.preventDefault(); // Prevent default form submission

    // Prevent duplicate submits when a session is being created
    if (window.checkoutInProgress) return;
    window.checkoutInProgress = true;

    // Disable card element so user cannot change input
    card.update({ 'disabled': true}); 

    // Disable submit button
    submitButton.disabled = true;
    submitButton.classList.add('disabled');
    submitButton.setAttribute('aria-disabled', 'true');

    // Show loading overlay with spinner
    loadingOverlay.classList.remove('d-none');

    // get data for cache

    // get membership tier from form
    const membershipTier = form.elements['membership_tier'].value;

    // Determine purchase_type from URL query param `purchase_type`
    const urlParams = new URLSearchParams(window.location.search);
    const purchaseType = urlParams.get('purchase_type');

    // get and trim checkout form values
    const fullName = form.full_name.value.trim();
    const email = form.email.value.trim();
    const phoneNumber = (form.phone_number.value || '').trim();
    const streetAddress1 = form.street_address1.value.trim();
    const streetAddress2 = (form.street_address2.value || '').trim();
    const townOrCity = (form.town_or_city.value || '').trim();
    const county = (form.county.value || '').trim();
    const postcode = form.postcode.value.trim();

    // Read amount from container data-attribute (template provides this)
    const amount = parseFloat(document.querySelector('[data-amount]').dataset.amount);

    const cacheData = {
        'payment_intent_id': paymentIntentId,
        'business_id': businessId,
        'membership_tier': membershipTier,
        'purchase_type': purchaseType,
        'full_name': fullName,
        'email': email,
        'phone_number': phoneNumber,
        'street_address1': streetAddress1,
        'street_address2': streetAddress2,
        'town_or_city': townOrCity,
        'county': county,
        'postcode': postcode,
        'amount': amount,
    };

    try {
        // Cache checkout data
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
        const resp = await fetch('/checkout/cache-checkout-data/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams(cacheData)
        });
        if (!resp.ok) throw new Error('Cache failed ' + resp.status);

        // Await payment confirmation from Stripe
        let result = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: card,
                billing_details: {
                    name: fullName,
                    email: email,
                    phone: phoneNumber,
                    address: {
                        line1: streetAddress1,
                        line2: streetAddress2,
                        city: townOrCity,
                        state: county,
                        country: 'GB',
                        postal_code: postcode,
                    }
                }
            }
        });

        if (result.error) {
            // payment failed (Stripe reported error)
            handleFailure(result.error.message, card);
        } else if (result.paymentIntent && result.paymentIntent.status === 'succeeded') {
            // payment succeeded: attach the PaymentIntent id to the form and submit
            document.querySelector('input[name="payment_intent_id"]').value = paymentIntentId;
            form.submit();
        }
    } catch (err) {
        handleFailure('There was a problem submitting your payment. Please check your details and try again.', card);
    }
});