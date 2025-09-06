from django.db import models
from django.conf import settings
from businesses.models import Business, MembershipTier
import uuid
from django.db import IntegrityError


class CheckoutCache(models.Model):
    """Tiny cache of checkout form data referenced from Stripe PaymentIntent metadata.

    We store a short server-side record and write only its id into the
    PaymentIntent metadata as `cc_ref`. This keeps PII out of Stripe.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    business_id = models.IntegerField(null=True, blank=True)
    membership_tier = models.IntegerField(null=True, blank=True)
    form_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'CheckoutCache {self.id}'

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
    
    # unique=True prevents duplicate PaymentIntent IDs
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    # Previously stored Stripe Price ID for membership; removed to keep the
    # codebase relying on local numeric pricing fields. If you need to store
    # the Stripe Price ID again add the field and run migrations.
    # Raw Stripe session payload for audit/reconciliation
    raw_payload = models.JSONField(blank=True, null=True)
    
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate purchase_number if not set. Retry on IntegrityError
        # to defend against the unlikely case of a purchase_number collision
        attempts = 0
        while True:
            if not self.purchase_number:
                self.purchase_number = uuid.uuid4().hex.upper()[:12]
            try:
                super().save(*args, **kwargs)
                break
            except IntegrityError:
                # If we hit a unique constraint (very rare), try a new number up to 3 times
                attempts += 1
                if attempts >= 3:
                    raise
                # regenerate and retry
                self.purchase_number = None

    def __str__(self):
        return f'Purchase {self.purchase_number} ({self.status})'
    