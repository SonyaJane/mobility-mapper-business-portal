document.addEventListener('DOMContentLoaded', () => {
  const stripe = Stripe(stripePublishableKey);
  const form = document.getElementById('checkout-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    try {
      const response = await fetch(createCheckoutSessionUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData,
      });
      const data = await response.json();
      if (data.error) {
        alert(data.error);
      } else {
        stripe.redirectToCheckout({ sessionId: data.session_id });
      }
    } catch (err) {
      console.error('Error creating Stripe Checkout session:', err);
      alert('There was an error initiating payment. Please try again.');
    }
  });
});
