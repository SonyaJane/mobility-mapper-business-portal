import stripe
import logging
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from businesses.models import Business, MembershipTier, WheelerVerificationRequest

from .forms import PurchaseForm
from .models import Purchase
from .models import CheckoutCache

logger = logging.getLogger(__name__)


@login_required
def checkout(request, business_id):
    # get Stripe API keys
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY
    # Set the currency of the checkout session
    currency = settings.STRIPE_CURRENCY
    # Get the business object
    business = get_object_or_404(Business, pk=business_id)

    if request.method == 'POST': 
        purchase_form = PurchaseForm(request.POST)
        if purchase_form.is_valid():
            
            # Get the PaymentIntent ID from the form data
            posted_pi = request.POST.get('payment_intent_id')
            # check if it exists
            if not posted_pi:
                return HttpResponse('missing payment intent', status=400)

            # Check if the PaymentIntent is valid
            stripe.api_key = stripe_secret_key
            try:
                intent = stripe.PaymentIntent.retrieve(posted_pi)
            except Exception:
                logger.exception('Failed to retrieve PaymentIntent %s', posted_pi)
                return HttpResponse('invalid payment intent', status=400)


            # Check if a Purchase already exists for this PaymentIntent
            purchase = Purchase.objects.filter(stripe_payment_intent_id=intent.id).first()
            # if not, create new Purchase
            if purchase is None:
                # determine purchase_type
                purchase_type = request.POST.get('purchase_type')
                # create new Purchase object and attach the PaymentIntent id
                purchase = purchase_form.save(commit=False)
                # attach the PaymentIntent id
                purchase.stripe_payment_intent_id = intent.id
                # convert purchase amount from the PaymentIntent (cents) to Decimal GBP
                pi_amount = int(intent.amount)
                purchase.amount = Decimal(pi_amount) / Decimal('100')
                # set the user who made the purchase
                purchase.user = request.user
                # get the business associated with the purchase
                purchase.business = business
                purchase.purchase_type = purchase_type
                # If membership_tier was submitted as an integer id, coerce to FK
                mt = request.POST.get('membership_tier')
                if mt:
                    try:
                        purchase.membership_tier_id = int(mt)
                    except Exception:
                        pass
                purchase.save()
            else:
                # update existing purchase with any new form data
                for field, value in purchase_form.cleaned_data.items():
                    setattr(purchase, field, value)
                # ensure amount remains set/updated
                pi_amount = int(intent.amount)
                purchase.amount = Decimal(pi_amount) / Decimal('100')
                purchase.save()

            # redirect to purchase_number URL
            return redirect(reverse('payment_success', args=[purchase.purchase_number]))

    else:  # GET
        # Get the purchase type
        purchase_type = request.GET.get('purchase_type')

        # Require ownership for verification purchases
        if purchase_type == 'verification':
            user_profile = getattr(request.user, 'userprofile', None)
            if business.business_owner != user_profile:
                return HttpResponseForbidden('You are not authorised to request verification for this business')

        if purchase_type == 'membership':
            # retrieve the selected membership tier pk
            membership_tier_pk = request.GET.get('membership_tier')
            # get the corresponding membership tier object
            membership_tier = MembershipTier.objects.filter(pk=int(membership_tier_pk)).first()
            # get the price and convert to pence
            # membership_price returns a Decimal
            amount = int((membership_tier.membership_price) * 100)
        else:
            # verification purchase
            # Get the existing membership tier object
            membership_tier = business.membership_tier  
            # get the price and convert to pence
            amount = int((membership_tier.verification_price) * 100)      
        

        # prepare initial form data        
        purchase_form = PurchaseForm(initial={
            'membership_tier': membership_tier.id if membership_tier else None,
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
        # Create the PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
        )
        client_secret = payment_intent.client_secret
        payment_intent_id = payment_intent.id
        
        # Get all paid membership tiers for context
        paid_membership_tiers = MembershipTier.objects.filter(is_active=True).exclude(tier='free')

        # Render the checkout template with the necessary context
        template = 'checkout/checkout.html'
        context = {
            'business': business,
            'form': purchase_form,
            'purchase_type': purchase_type,
            'stripe_public_key': stripe_public_key,
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


@require_POST
@login_required
def cache_checkout_data(request):
    """Cache checkout form data on the Stripe PaymentIntent so webhooks can
    retrieve it later. Accepts form-encoded POST body.
    Expects a 'payment_intent_id' field and checkout fields: membership_tier,
    purchase_type, full_name, email, phone, and address fields. Attaches them to the
    PaymentIntent metadata.
    """
    # Parse incoming data from POST payload
    try:
        payload = request.POST

        pid = payload.get('payment_intent_id')

        # Persist form data server-side in CheckoutCache and link to PI by id
        cache = CheckoutCache.objects.create(
            payment_intent_id=pid,
            user=request.user if request.user.is_authenticated else None,
            business_id=payload.get('business_id') or None,
            membership_tier=payload.get('membership_tier') or None,
            form_data={
                'purchase_type': payload.get('purchase_type', ''),
                'full_name': payload.get('full_name', ''),
                'email': payload.get('email', ''),
                'phone_number': payload.get('phone_number', ''),
                'street_address1': payload.get('street_address1', ''),
                'street_address2': payload.get('street_address2', ''),
                'town_or_city': payload.get('town_or_city', ''),
                'county': payload.get('county', ''),
                'postcode': payload.get('postcode', ''),
                'amount': payload.get('amount') or None,
            }
        )

        # Attach only a short cache reference to the PaymentIntent metadata
        stripe.api_key = settings.STRIPE_SECRET_KEY  # required to modify PaymentIntent
        stripe.PaymentIntent.modify(pid, metadata={'cc_ref': str(cache.id)})

        return HttpResponse(status=200)
    except Exception as e:
        logger.exception('Failed to cache checkout data for PaymentIntent %s', locals().get('pi_id'))
        messages.error(request, 'Sorry, your payment cannot be processed right now. Please try again later.')
        return HttpResponse(content=str(e), status=400)

