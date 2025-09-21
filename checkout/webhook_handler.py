# handles signals (webhooks) from Stripe when an event occurs
# We specify URL the signals are sent to
# The webhook handler determines what we want to given a particular event signal
import stripe

from django.db import IntegrityError
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Purchase, CheckoutCache
from businesses.models import Business, MembershipTier


class StripeWebHookHandler:
    """
        Handle Stripe webhooks
        For each type of webhook, we have a different method to handle it
    """
    # assign the request as an attribute of the class so we can 
    # access any attributes of the request coming from Stripe.
    def __init__(self, request):
        self.request = request

    def _send_confirmation_email(self, purchase):
        """Send the user a confirmation email"""
        cust_email = purchase.email
        print(f'cust_email: {cust_email}')
        subject = render_to_string(
            'checkout/confirmation_emails/confirmation_email_subject.txt',
            {'purchase': purchase})
        print(f'subject: {subject}')
        body = render_to_string(
            'checkout/confirmation_emails/confirmation_email_body.txt',
            {'purchase': purchase, 'contact_email': settings.DEFAULT_FROM_EMAIL})
        print(f'body: {body}')
        print(f'from_email: {settings.DEFAULT_FROM_EMAIL}')
        
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [cust_email],
            fail_silently=False
        )

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        return HttpResponse(
            content=f'Unhandled webhook received: {event["type"]}',
            status=200)

    def handle_payment_intent_succeeded(self, event):
        """
        Handle the payment_intent.succeeded webhook from Stripe
        """
        intent = event.data.object
        pid = intent.get('id')
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Try to find an existing Purchase by the PaymentIntent id
        purchase = Purchase.objects.filter(stripe_payment_intent_id=pid).first()
        # If there isn't a Purchase, create one using metadata stored on the PI
        if purchase is None:
            # Use the server-side cache data in a CheckoutCache object referenced by
            # cc_ref in PI metadata to create the Purchase (defensively)
            metadata = intent.get('metadata') or {}
            cc_ref = metadata.get('cc_ref')
            cache = CheckoutCache.objects.filter(id=cc_ref).first() if cc_ref else None
            form = getattr(cache, 'form_data', {}) or {}
            # Attach business and membership tier from the cache top-level fields
            biz_id = getattr(cache, 'business_id', None)
            tier_id = getattr(cache, 'membership_tier', None)
            # Merge business/tier into metadata so later upgrade logic can find them
            metadata['business_id'] = str(biz_id)
            metadata['membership_tier'] = str(tier_id)

            try:
                purchase, created = Purchase.objects.get_or_create(
                    stripe_payment_intent_id=pid,
                    defaults={
                        'purchase_type': form.get('purchase_type', 'membership'),
                        'full_name': form.get('full_name', ''),
                        'email': form.get('email', ''),
                        'phone_number': form.get('phone_number', ''),
                        'street_address1': form.get('street_address1', ''),
                        'street_address2': form.get('street_address2', ''),
                        'town_or_city': form.get('town_or_city', ''),
                        'county': form.get('county', ''),
                        'postcode': form.get('postcode', ''),
                        'amount': (intent.get('amount') or 0) / 100.0,
                        'raw_payload': intent,
                        'metadata': metadata,
                        'business': Business.objects.filter(pk=biz_id).first() if biz_id else None,
                        'membership_tier': MembershipTier.objects.filter(pk=tier_id).first() if tier_id else None,
                    }
                )
            except IntegrityError:
                # concurrent create raced us; re-fetch the purchase
                purchase = Purchase.objects.filter(stripe_payment_intent_id=pid).first()
            
        # Update existing purchase status and payload
        if purchase:
            purchase.status = 'completed'
            purchase.raw_payload = intent
            purchase.metadata = intent.get('metadata', {}) or {}

            purchase.save()
            biz_id = purchase.business.id
            tier_id = purchase.membership_tier.id
            # If this was a membership purchase, upgrade the Business tier.
            business = Business.objects.filter(pk=int(biz_id)).first()
            purchase_type = purchase.purchase_type
            biz_id = purchase.business.id
            tier_id = purchase.membership_tier.id

            if purchase_type == 'membership':
                tier = MembershipTier.objects.filter(pk=int(tier_id)).first()
                business.membership_tier = tier
                business.save()

            # If this was a verification purchase, set verification_requested to true
            if purchase_type == 'verification':
                business.wheeler_verification_requested = True
                business.save()
                
            self._send_confirmation_email(purchase)

        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)

    def handle_payment_intent_payment_failed(self, event):
        """
        Handle the payment_intent.payment_failed webhook from Stripe
        """
        intent = event.data.object
        pid = intent.get('id')
        purchase = None
        if pid:
            purchase = Purchase.objects.filter(stripe_payment_intent_id=pid).first()
        if purchase:
            purchase.status = 'canceled'
            purchase.raw_payload = intent
            purchase.metadata = intent.get('metadata', {}) or {}
            purchase.save()

        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
