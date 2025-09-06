## Stripe Payment Flow using PaymentIntent

This section describes the checkout process used by the project.

Below is a step-by-step flow showing how the code implements checkout with Stripe PaymentIntents. 

### Step-by-step implementation flow

**1. Authentication and ownership**
- Enter checkout view - GET handler. The view requires an authenticated user (it is protected by login). For verification purchases the view validates that the requesting user is authorised to request verification for the target `Business` (it compares business.business_owner with user_profile). If the user is not authorised the view returns HTTP 403.

**2. Routes that lead to checkout**
- From the Register Business flow (user selected tier) — the register view redirects to checkout with `?membership_tier=<id>&purchase_type=membership`.
- From Explore Memberships (user chooses an upgrade) — upgrade links include `?membership_tier=<id>&purchase_type=membership`.
- From Request Wheeler Verification — the verification page POSTs to the `request_wheeler_verification` view. That view computes the verification price from the business's membership tier; if the computed amount is zero it sets `business.wheeler_verification_requested = True` and skips checkout, otherwise it redirects to checkout with `?purchase_type=verification` (the `business_id` is still passed as the URL path arg).

**3. What the checkout view supports**
- The same `checkout` view handles two kinds of purchases: `membership` and `verification`.
- `purchase_type` is read from query parameters. Valid values are the strings `membership` and `verification`.

**4. How the view determines the membership tier and amount**
- For `membership` flows the GET handler expects a query param `membership_tier` containing the MembershipTier primary key, with which it grabs the corresponding MembershipTier object. The view then gets the `membership_price` from this object and converts it into pence.
- For `verification` flows the business already exists, so the server gets the membership_tier ForeignKey from the Business object, and grabs the corresponding MembershipTier. The view then gets the `verification_price` from this object and converts it into pence.

**5. Initial form population**
- Next, the view pre-fills the `PurchaseForm` from available data on `request.user` and from the `Business` (full name, email, phone, street_address*, town_or_city, county, postcode). This improves UX and reduces typing for the user.

**6. PaymentIntent creation**
- The server creates a Stripe PaymentIntent with the computed amount (in the smallest currency unit, pence) and currency using the secret API key. The returned PaymentIntent contains a client_secret (required by the browser to confirm the PaymentIntent with Stripe Elements) and an id (used as the authoritative reference, saved on the Purchase and used by webhooks).

**7. render/context block**
- Finally, the view builds a `context` dict containing the `client_secret` and `payment_intent_id` (alongside `business`, `form`, `amount`, etc.) and calls `render(request, template, context)`.
- The template exposes these values to browser JS safely (the project uses Django's `json_script`), so client code can read them with `JSON.parse(document.getElementById('id_client_secret').textContent)` and confirm the PaymentIntent with Stripe Elements.

**8. Client review and card entry**
- After the checkout page loads, the client reviews the pre-filled form and types card details into the Stripe Element.

**9. Cache checkout data**
- When the user clicks the submit button, the client (checkout.js) first posts the non-card checkout fields to the `cache_checkout_data` endpoint so the server can persist the data in a `CheckoutCache` record, and updates the PaymentIntent metadata to include a short reference token (`cc_ref`) that points to that cache record.

**10. Confirm the PaymentIntent**
- The client then calls `stripe.confirmCardPayment` with the card elements and billing deails to confirm the PI and complete card authentication.

**11. Client POST: create/update Purchase**
- On successful confirmation, client inserts the `payment_intent_id` into the checkout form and performs a normal POST back to the server (`checkout` view - POST handler) to create or update a `Purchase` record.

**12. Server POST handler behaviour**
- The server POST handler in the `checkout` view checks for an existing Purchase with that payment intent id. If found it updates it, otherwise it creates a new Purchase and sets `amount` (Decimal GBP) before saving.

**13. Webhook authoritative processing**
- Stripe sends a `payment_intent.succeeded` webhook (authoritative). The webhook handler verifies the event, reads `intent.metadata['cc_ref']`, loads the corresponding `CheckoutCache`, and attempts to create a `Purchase` using the server-stored form data found in `CheckoutCache.form_data`. The webhook sets the authoritative `amount` from the PaymentIntent (intent.amount / 100).

**14. Membership upgrade behaviour**
- When the purchase is of type `membership`, the webhook upgrades the `Business`'s `membership_tier`. The upgrade code gets `business_id` and `membership_tier` from the Purchase instance. 
- When the purchase is of type `verification`, the webhook sets the `Business`'s `wheeler_verification_requested` attribute to `True`.

**15. Idempotency and redirect**
- Webhook processing is idempotent: duplicate webhooks or race conditions (webhook before POST and vice-versa) will not create duplicate Purchase records because the code looks up by `stripe_payment_intent_id` and uses the `cc_ref` server cache; a unique DB constraint on `stripe_payment_intent_id` prevents duplicates.
- User is redirected to a `payment_success` page which uses the server-generated `purchase_number` as the public reference.
