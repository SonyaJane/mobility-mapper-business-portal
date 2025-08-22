from django.db import models
from django.conf import settings
import uuid

class Order(models.Model):
    """Model to track Stripe orders and their status."""
    
    # Type of order: subscription or one-off verification
    ORDER_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('verification', 'One-off Verification'),
    ]
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
        # Tier for subscriptions (standard vs premium)
    TIER_CHOICES = [
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    # Billing interval for subscriptions
    INTERVAL_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    # Unique order number for reference
    order_number = models.CharField(max_length=32, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(max_length=254, null=False, blank=False)
    
    phone_number = models.CharField(max_length=20, null=False, blank=False)
    street_address1 = models.CharField(max_length=80, null=False, blank=False)
    street_address2 = models.CharField(max_length=80, null=True, blank=True)
    town_or_city = models.CharField(max_length=40, null=False, blank=False)
    county = models.CharField(max_length=80, null=True, blank=True)
    postcode = models.CharField(max_length=20, null=True, blank=True)
    
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, blank=True, null=True)
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES, blank=True, null=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)    
    
    stripe_checkout_session_id = models.CharField(max_length=255, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order {self.order_number} ({self.status})'

    def save(self, *args, **kwargs):
        # Generate order_number if not set
        if not self.order_number:
            self.order_number = uuid.uuid4().hex.upper()[:12]
        super().save(*args, **kwargs)
