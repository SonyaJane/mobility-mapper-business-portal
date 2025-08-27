from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.conf import settings
import stripe
from businesses.models import Business, PricingTier
from .forms import OrderForm
from django.contrib import messages

def checkout_subscription(request, business_id):
    # Load business and query params
    business = get_object_or_404(Business, pk=business_id)
    tier = request.GET.get('tier')

    # Load all active pricing tiers
    # Load all active pricing tiers except the free tier
    pricing_tiers = PricingTier.objects.filter(is_active=True).exclude(tier='free')
    # get Stripe API keys
    stripe_public_key = settings.STRIPE_PUBLISHABLE_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY
    
    # Determine Stripe Price ID based on interval
    price_id = None
    if business.pricing_tier:
        if interval == 'yearly' and business.pricing_tier.stripe_annual_price_id:
            price_id = business.pricing_tier.stripe_annual_price_id
        else:
            price_id = business.pricing_tier.stripe_monthly_price_id
    
    # Initialize checkout form with defaults (prepopulate contact and address)
    form_initial = {
        'order_type': 'subscription',
        'tier': tier,
        'interval': interval,
        # Prepopulate contact and address fields
        'full_name': f"{request.user.first_name} {request.user.last_name}".strip() if request.user.is_authenticated else '',
        'email': request.user.email if request.user.is_authenticated else '',
        'phone_number': business.contact_phone or business.public_phone or '',
        'street_address1': business.street_address1 or '',
        'street_address2': business.street_address2 or '',
        'town_or_city': business.town_or_city or '',
        'county': business.county or '',
        'postcode': business.postcode or '',
    }
    form = OrderForm(initial=form_initial)
    return render(request, 'checkout/checkout_subscription.html', {
        'business': business,
        'form': form,
        'stripe_publishable_key': stripe_public_key,
        'client_secret': stripe_secret_key,
        'pricing_tiers': pricing_tiers,  # Pass pricing_tiers to template context
    })


def checkout_wheeler_verification(request, business_id):
    business = get_object_or_404(Business, pk=business_id)
    stripe_public_key = settings.STRIPE_PUBLISHABLE_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    if request.method == 'POST':
        # POST: process payment
        order_form = OrderForm(request.POST)
        if order_form.is_valid():
            data = order_form.cleaned_data
            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': data['stripe_price_id'],
                    'quantity': 1,
                }],
                'mode': 'payment',
                'success_url': request.build_absolute_uri(reverse('payment_success')),
                'cancel_url': request.build_absolute_uri(reverse('payment_failed')),
            }
            try:
                session = stripe.checkout.Session.create(**session_params)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.stripe_checkout_session_id = session.id
            order.save()
            return JsonResponse({'session_id': session.id})
    
        else:
            messages.error(request, 'There was an error with your form. \
                Please double check your information.')

    else:
        # GET: render checkout page
        tier = business.pricing_tier.tier if business.pricing_tier else 'free'
        total = 60 if tier == 'free' else 30
        stripe.api_key = stripe_secret_key
        intent = stripe.PaymentIntent.create(
            amount=int(total * 100),
            currency=settings.STRIPE_CURRENCY,
        )
        form_initial = {
            'order_type': 'wheeler_verification',
            'tier': tier,
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip() if request.user.is_authenticated else '',
            'email': request.user.email if request.user.is_authenticated else '',
            'phone_number': business.contact_phone or business.public_phone or '',
            'street_address1': business.street_address1 or '',
            'street_address2': business.street_address2 or '',
            'town_or_city': business.town_or_city or '',
            'county': business.county or '',
            'postcode': business.postcode or '',
        }
        form = OrderForm(initial=form_initial)
        if not stripe_public_key:
            messages.warning(request, 'Stripe public key is missing. Did you forget to set it in your environment?')
        return render(request, 'checkout/checkout_wheeler_verification.html', {
            'business': business,
            'form': form,
            'tier': tier,
            'total': total,
            'stripe_publishable_key': stripe_public_key,
            'client_secret': intent.client_secret,
        })

    

def payment_success(request):
    return render(request, 'checkout/payment_success.html')

def payment_failed(request):
    return render(request, 'checkout/payment_failed.html')
