import json
import stripe
import logging

from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from businesses.models import Business, MembershipTier, WheelerVerificationRequest

from .forms import PurchaseForm
from .models import Purchase

logger = logging.getLogger(__name__)


@login_required
def checkout(request, business_id):
    # get Stripe API keys
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    currency = settings.STRIPE_CURRENCY
    
    business = get_object_or_404(Business, pk=business_id)
    # Load all active membership tiers except the free tier
    paid_membership_tiers = MembershipTier.objects.filter(is_active=True).exclude(tier='free')

    # Get purchase type 
    if request.method == 'POST':
        purchase = request.POST.get('purchase')
    else:
        purchase = request.GET.get('purchase') 
    print('purchase:', purchase)
    
    # Get membership tier membership_tier and price_id
    membership_tier = business.membership_tier
    print('membership_tier 1', membership_tier)
    # Allow overriding membership_tier via GET param on initial render so selecting
    # a tier from the UI reloads the page with the chosen tier and the server
    # creates a PaymentIntent for that tier.
    if request.method == 'GET':
        param_tier = request.GET.get('membership_tier')
        if param_tier:
            membership_tier = MembershipTier.objects.filter(pk=int(param_tier)).first()
            print('membership_tier 2', membership_tier)

    if purchase == 'membership':
        # Use the business's current or requested tier
        price_id = membership_tier.membership_stripe_price_id if membership_tier else None
        covered = False  # Memberships are never covered
        amount = int((membership_tier.price or 0) * 100) if membership_tier else 0
    else:
        # verification purchase
        # Determine price_id and covered based on existing membership tier
        if membership_tier == 'premium':
            covered = True
            price_id = None
        else:
            # standard or free 
            covered = False
            price_id = membership_tier.verification_stripe_price_id if membership_tier else None
            # Use verification_price with fallback to price; guard missing tier
            if membership_tier:
                v_price = getattr(membership_tier, 'verification_price', None)
                amount = int((v_price if v_price is not None else (membership_tier.price or 0)) * 100)
            else:
                amount = 0

    if request.method == 'POST':        
        purchase_form = PurchaseForm(request.POST)
        print('purchase_form:', purchase_form)   
        if purchase_form.is_valid():
            print('purchase_form is valid')
            # save purchase to database
            purchase = purchase_form.save()
            # redirect to success page
            return redirect(reverse('checkout:payment_success', args=[purchase.purchase_number]))

    else:
        # GET: prepare initial form data        
        purchase_form = PurchaseForm(initial={
            'membership_tier': membership_tier.id,
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'email': request.user.email,
            'phone_number': business.contact_phone or business.public_phone or '',
            'street_address1': business.street_address1 or '',
            'street_address2': business.street_address2 or '',
            'town_or_city': business.town_or_city or '',
            'county': business.county or '',
            'postcode': business.postcode or '',
        })

        # Create a PaymentIntent
        stripe.api_key = stripe_secret_key
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata={
                'business_id': str(business.id),
                'purchase': purchase,
                'membership_tier': str(membership_tier.id),
                'user_id': str(request.user.id),
            }
        )
        client_secret = payment_intent.client_secret
        payment_intent_id = payment_intent.id

        # Render the checkout template with the necessary context
        template = 'checkout/checkout.html'
        context = {
                'business': business,
                'form': purchase_form,
                'purchase': purchase,
                'covered': covered,
                'stripe_public_key': stripe_public_key,
                'price_id': price_id,
                'business_id': business.id,
                'paid_membership_tiers': paid_membership_tiers,
                'membership_tier': membership_tier,
                'client_secret': client_secret,
                'payment_intent_id': payment_intent_id,
                'amount': amount/100,
            }
        return render(request, template, context)


def payment_success(request, purchase_number):
    # get the purchase
    purchase= get_object_or_404(Purchase, purchase_number=purchase_number)
    
    template = 'checkout/payment_success.html'
    context = {
        'purchase': purchase,
    }
    return render(request, template , context)

def payment_failed(request):
    return render(request, 'checkout/payment_failed.html')


def payment_status(request):
    """AJAX endpoint: given ?payment_intent_id=..., return JSON status and purchase info if available."""
    payment_intent_id = request.GET.get('payment_intent_id')
    if not payment_intent_id:
        return JsonResponse({'error': 'missing_payment_intent_id'}, status=400)
    # payment_intent_id is expected to be a PaymentIntent id (pi_...)
    purchase = Purchase.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
    if purchase:
        return JsonResponse({
            'status': 'completed',
            'purchase_number': purchase.purchase_number,
            'amount': float(purchase.amount),
            'tier_display': purchase.membership_tier.get_tier_display() if purchase.membership_tier else '',
        })
    return JsonResponse({'status': 'pending'})

# local helper to centralise tolerant webhook error logging.
def _log_webhook_error(message, context=None):
    """Log an exception for webhook processing with optional context.

    This helper is intentionally tolerant: any error during logging is
    swallowed so webhook handling never raises additional exceptions.
    """
    try:
        extra = {'webhook_context': context or {}}
        # Use logger.exception so the current exception info is included.
        logger.exception(message, extra=extra)
    except Exception:
        try:
            logger.error(message)
        except Exception:
            # Last-resort: do nothing to avoid bubbling errors from logging.
            pass

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = json.loads(payload)
    except ValueError:
        # Malformed payload
        _log_webhook_error('Webhook processing error (parse_payload)', {'stage': 'parse_payload', 'payload_length': len(payload) if payload is not None else 0})
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        _log_webhook_error('Webhook processing error (signature_verification)', {'stage': 'signature_verification', 'sig_header_present': bool(sig_header)})
        return HttpResponse(status=400)

    # We only handle PaymentIntent webhooks (payment_intent.succeeded) for the on-site Elements flow.

    # continue to other event handlers (e.g. payment_intent.succeeded)

    # Handle PaymentIntent succeeded (for on-site Elements flow)
    if event['type'] == 'payment_intent.succeeded':
        try:
            raw_pi = event['data']['object']
            pi_id = raw_pi.get('id')
            stripe.api_key = settings.STRIPE_SECRET_KEY
            # Retrieve full PaymentIntent to access charges and metadata
            pi = stripe.PaymentIntent.retrieve(pi_id, expand=['charges.data.billing_details'])

            metadata = pi.get('metadata', {})
            business_id = metadata.get('business_id')
            purchase = metadata.get('purchase')
            membership_tier_id = metadata.get('membership_tier') or None

            # Extract amount and customer details
            amount_total = 0
            if pi.get('amount') is not None:
                amount_total = pi['amount'] / 100.0
            billing_details = {}
            charges = pi.get('charges', {}).get('data', [])
            if charges:
                billing_details = charges[0].get('billing_details') or {}
            full_name = billing_details.get('name') or ''
            email = billing_details.get('email') or ''
            phone = billing_details.get('phone') or ''
            address = billing_details.get('address') or {}
            street1 = address.get('line1') or ''
            street2 = address.get('line2') or ''
            city = address.get('city') or ''
            state = address.get('state') or ''
            postal = address.get('postal_code') or ''

            # Resolve related models
            user = None
            User = get_user_model()
            if metadata.get('user_id'):
                try:
                    user = User.objects.filter(pk=int(metadata.get('user_id'))).first()
                except Exception:
                    user = None

            membership_tier = None
            if membership_tier_id:
                try:
                    membership_tier = MembershipTier.objects.filter(pk=int(membership_tier_id)).first()
                except Exception:
                    membership_tier = None

            business = None
            if business_id:
                try:
                    business = Business.objects.filter(pk=int(business_id)).first()
                except Exception:
                    business = None

            # Idempotency: skip if an Purchase with this payment intent id already exists
            existing = Purchase.objects.filter(stripe_payment_intent_id=pi.get('id')).first()
            if existing:
                logger.info('Received webhook for already-processed PaymentIntent %s; skipping', pi.get('id'))
                return HttpResponse(status=200)

            try:
                purchase = Purchase.objects.create(
                    user=user,
                    full_name=full_name or ' ',
                    email=email or ' ',
                    phone_number=phone or ' ',
                    street_address1=street1 or ' ',
                    street_address2=street2 or '',
                    town_or_city=city or ' ',
                    county=state or ' ',
                    postcode=postal or ' ',
                    purchase_type='verification' if purchase == 'verification' else 'membership',
                    membership_tier=membership_tier,
                    amount=amount_total,
                    stripe_payment_intent_id=pi.get('id'),
                    membership_stripe_price_id='',
                    status='completed'
                )
                try:
                    if isinstance(pi, dict):
                        purchase.raw_payload = pi
                    else:
                        purchase.raw_payload = pi.to_dict()
                    purchase.save()
                except Exception:
                    _log_webhook_error('Webhook processing error (save_raw_payload) for payment_intent %s' % pi_id, {'stage': 'save_raw_payload', 'payment_intent_id': pi_id, 'purchase_id': getattr(purchase, 'id', None)})
            except Exception:
                _log_webhook_error('Webhook processing error (create_purchase) for payment_intent %s' % pi_id, {'stage': 'create_purchase', 'payment_intent_id': pi_id})

            # Fulfil purchase: mirror the logic used for sessions
            if purchase == 'membership' and business and membership_tier:
                try:
                    business.membership_tier = membership_tier
                    business.save()
                    try:
                        owner_email = None
                        if hasattr(business.business_owner, 'user') and getattr(business.business_owner.user, 'email', None):
                            owner_email = business.business_owner.user.email
                        if owner_email:
                            profile_name = business.business_owner.get_full_name() if hasattr(business.business_owner, 'get_full_name') else str(business.business_owner)
                            context = {
                                'profile_name': profile_name,
                                'business_name': business.business_name,
                                'tier_display': membership_tier.get_tier_display() if membership_tier else '',
                            }
                            text_body = render_to_string('checkout/emails/membership_received.txt', context)
                            html_body = render_to_string('checkout/emails/membership_received.html', context)
                            send_mail(
                                subject='Your business membership payment was received',
                                message=text_body,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[owner_email],
                                fail_silently=True,
                                html_message=html_body,
                            )
                    except Exception:
                        logger.exception('Failed to send membership notification email for business %s', business_id)
                except Exception:
                    logger.exception('Failed to assign membership tier for business %s', business_id)

            if purchase == 'verification' and business:
                try:
                    if user:
                        existing_req = WheelerVerificationRequest.objects.filter(business=business, wheeler=user).first()
                        if existing_req:
                            req = existing_req
                        else:
                            try:
                                req = WheelerVerificationRequest.objects.create(business=business, wheeler=user)
                            except IntegrityError:
                                req = WheelerVerificationRequest.objects.filter(business=business, wheeler=user).first()
                        try:
                            if user.email:
                                context = {
                                    'user_name': user.get_full_name() or user.username,
                                    'business_name': business.business_name,
                                    'request_id': req.id,
                                }
                                text_body = render_to_string('checkout/emails/verification_received.txt', context)
                                html_body = render_to_string('checkout/emails/verification_received.html', context)
                                send_mail(
                                    subject='Your verification payment was received',
                                    message=text_body,
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[user.email],
                                    fail_silently=True,
                                    html_message=html_body,
                                )
                        except Exception:
                            logger.exception('Failed to send verification notification email to user %s', user.id)
                    else:
                        logger.info('Verification payment received for business %s but no user_id in metadata', business_id)
                except Exception:
                    logger.exception('Failed to create WheelerVerificationRequest for business %s', business_id)

        except Exception:
            _log_webhook_error('Webhook processing error (handle_payment_intent) for payment_intent %s' % (pi_id if 'pi_id' in locals() else None), {'stage': 'handle_payment_intent', 'payment_intent_id': pi_id if 'pi_id' in locals() else None})

        return HttpResponse(status=200)
