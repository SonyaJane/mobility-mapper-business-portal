from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.conf import settings
import stripe
from businesses.models import Business
from .forms import CheckoutForm

def checkout(request, business_id):
    # Load business and query params
    business = get_object_or_404(Business, pk=business_id)
    tier = request.GET.get('tier')
    interval = request.GET.get('billing_frequency')
    # Determine Stripe Price ID based on interval
    price_id = None
    if business.pricing_tier:
        if interval == 'yearly' and business.pricing_tier.stripe_annual_price_id:
            price_id = business.pricing_tier.stripe_annual_price_id
        else:
            price_id = business.pricing_tier.stripe_monthly_price_id
    # Initialize checkout form with defaults
    form_initial = {
        'order_type': 'subscription',
        'tier': tier,
        'interval': interval,
        'stripe_price_id': price_id,
    }
    form = CheckoutForm(initial=form_initial)
    return render(request, 'checkout/checkout.html', {
        'business': business,
        'form': form,
    })

@require_POST
def create_checkout_session(request):
    """Create Stripe Checkout session and return its ID."""
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form data'}, status=400)
    data = form.cleaned_data
    stripe.api_key = settings.STRIPE_SECRET_KEY
    # Build session parameters
    session_params = {
        'payment_method_types': ['card'],
        'line_items': [{
            'price': data['stripe_price_id'],
            'quantity': 1,
        }],
        'mode': 'subscription' if data['order_type'] == 'subscription' else 'payment',
        'success_url': request.build_absolute_uri(reverse('payment_success')),
        'cancel_url': request.build_absolute_uri(reverse('payment_failed')),
    }
    # Create Stripe session
    try:
        session = stripe.checkout.Session.create(**session_params)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    # Save order
    order = form.save(commit=False)
    if request.user.is_authenticated:
        order.user = request.user
    order.stripe_checkout_session_id = session.id
    # Save subscription ID if present
    if hasattr(session, 'subscription') and session.subscription:
        order.stripe_subscription_id = session.subscription
    order.save()
    return JsonResponse({'session_id': session.id})

def payment_success(request):
    return render(request, 'checkout/payment_success.html')

def payment_failed(request):
    return render(request, 'checkout/payment_failed.html')
