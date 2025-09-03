from django.db import models
from django.conf import settings
from businesses.models import Business, MembershipTier
import uuid

class Purchase(models.Model):
    """Model to track Stripe purchases and their status."""

    # Type of purchase: membership or verification
    PURCHASE_TYPE_CHOICES = [
        ('membership', 'Membership for one year'),
        ('verification', 'Verification of Accessibility Features'),
    ]
    PURCHASE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    # Memberships tiers
    TIER_CHOICES = [
        ('free', 'Free'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    # Unique purchase number for reference
    purchase_number = models.CharField(max_length=32, unique=True, blank=True)
    purchase_type = models.CharField(max_length=20, choices=PURCHASE_TYPE_CHOICES)

    # Foreign keys
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True)
    membership_tier = models.ForeignKey(MembershipTier, on_delete=models.SET_NULL, null=True, blank=True)

    full_name = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(max_length=254, null=False, blank=False)
    
    phone_number = models.CharField(max_length=20, null=False, blank=False)
    street_address1 = models.CharField(max_length=80, null=False, blank=False)
    street_address2 = models.CharField(max_length=80, null=True, blank=True)
    town_or_city = models.CharField(max_length=40, null=False, blank=False)
    county = models.CharField(max_length=80, null=False, blank=False)
    postcode = models.CharField(max_length=20, null=False, blank=False)
    
    # purchase status using defined choices
    status = models.CharField(
        max_length=20,
        choices=PURCHASE_STATUS_CHOICES,
        default='pending'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)    
    
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    membership_stripe_price_id = models.CharField(max_length=255)
    # Raw Stripe session payload for audit/reconciliation
    raw_payload = models.JSONField(blank=True, null=True)
    
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate purchase_number if not set
        if not self.purchase_number:
            self.purchase_number = uuid.uuid4().hex.upper()[:12]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Purchase {self.purchase_number} ({self.status})'
    