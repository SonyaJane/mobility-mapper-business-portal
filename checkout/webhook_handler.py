# handles signals (webhooks) from Stripe when an event occurs
# We specify URL the signals are sent to
# The webhook handler determines what we want to given a particular event signal 
from django.http import HttpResponse
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
#from django.conf import settings

# from .models import Purchase
# from accounts.models import UserProfile


# import json
# import time


class StripeWebHookHandler:
    """
        Handle Stripe webhooks
        For each type of webhook, we have a different method to handle it
    """
    # assign the request as an attribute of the class so we can 
    # access any attributes of the request coming from Stripe.
    def __init__(self, request):
        self.request = request

    # def _send_confirmation_email(self, order):
    #     """Send the user a confirmation email"""
    #     cust_email = order.email
    #     subject = render_to_string(
    #         'checkout/confirmation_emails/confirmation_email_subject.txt',
    #         {'order': order})
    #     body = render_to_string(
    #         'checkout/confirmation_emails/confirmation_email_body.txt',
    #         {'order': order, 'contact_email': settings.DEFAULT_FROM_EMAIL})

    #     send_mail(
    #         subject,
    #         body,
    #         settings.DEFAULT_FROM_EMAIL,
    #         [cust_email]
    #     )

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
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
        
    def handle_payment_intent_payment_failed(self, event):
        """
        Handle the payment_intent.payment_failed webhook from Stripe
        """
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
