from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .webhook_handler import StripeWebHookHandler
import stripe

@require_POST
@csrf_exempt
def webhook(request):
    """Listen for webhooks from Stripe"""
    # webhook secret, used to verify that the webhook actually came from strip
    wh_secret = settings.STRIPE_WH_SECRET
    # Stripe secret API key
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # get the webhook data and verify its signature
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WH_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # generic exception handler
    except Exception as e:
        return HttpResponse(content=e, status=400)

    # Set up a webhook handler
    handler = StripeWebHookHandler(request)
    # Map webhook events to relevant handler functions
    event_map = {
        'payment_intent.succeeded': handler.handle_payment_intent_succeeded,
        'payment_intent.payment_failed': handler.handle_payment_intent_payment_failed,
    }
    # Get the webhook type from Stripe, which contains something like 
    # payment intent.succeeded or payment intent.payment failed
    event_type = event['type']
    
    # Look up the event type in the event map, get the corresponding 
    # event handler, and give it the alias event_handler
    event_handler = event_map.get(event_type, handler.handle_event)
    
    # Call the event handler with the event
    response = event_handler(event)
    # return the response to Stripe
    return response