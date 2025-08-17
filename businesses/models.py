"""
Models for the businesses app, including PricingTier, Business, and WheelerVerification.
Defines business tiers, business details, and accessibility/verification features.
"""

from django.contrib.gis.db import models as geomodels
from django.db import models
from django.conf import settings
from cloudinary_storage.storage import MediaCloudinaryStorage

TIER_CHOICES = [
    ('free', 'Free'),
    ('standard', 'Standard'),
    ('premium', 'Premium'),
]

BILLING_FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly (Save up to 20%)'),
    ]
    
class PricingTier(models.Model):
    """
    Represents a subscription/pricing tier for businesses.
    Includes monthly and optional yearly pricing, Stripe integration, tier type, and active status.
    """
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free', help_text="Tier type (free, supporter, featured)")
    description = models.TextField(blank=True)
    price_per_month = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_year = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    stripe_monthly_price_id = models.CharField(max_length=100, help_text="The Stripe Price ID for this tier")
    stripe_annual_price_id = models.CharField(max_length=100, blank=True, help_text="The Stripe Price ID for yearly billing")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """String representation showing name and prices."""
        prices = [f"£{self.price_per_month}/mo"]
        if self.price_per_year:
            prices.append(f"£{self.price_per_year}/yr")
        return f"{self.tier} ({', '.join(prices)})"


class AccessibilityFeature(models.Model):
    """
    Represents an accessibility feature (e.g., Step-free access).
    """
    code = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Represents a business category (e.g., Café, Retail Store).
    """
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    group_code = models.CharField(max_length=30, blank=True, null=True, help_text="Group code for category grouping (e.g. 'retail', 'food_drink')")
    group_description = models.CharField(max_length=200, blank=True, null=True, help_text="Description of the group (e.g. 'Retail', 'Food & Drink')")
    tags = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.group_description})" if self.group_description else self.name

    class Meta:
        verbose_name_plural = "Categories"


class Business(models.Model):
    """
    Represents a business registered on the platform.
    Stores owner, details, location, accessibility, pricing tier, and verification info.
    """
    class Meta:
        verbose_name_plural = "Businesses"
    # Owner is a UserProfile, which extends the User model
    business_owner = models.OneToOneField('accounts.UserProfile', on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = geomodels.PointField(geography=True)
    address = models.CharField(max_length=300)
    categories = models.ManyToManyField('Category', blank=True, related_name='businesses')
    accessibility_features = models.ManyToManyField('AccessibilityFeature', blank=True, related_name='businesses')
    logo = models.ImageField(
        upload_to='business_logos/',
        storage=MediaCloudinaryStorage(),
        blank=True,
        null=True,
    )
    website = models.URLField(blank=True, null=True)
    opening_hours = models.TextField(blank=True, null=True)
    public_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    public_email = models.EmailField(blank=True, null=True)
    services_offered = models.TextField(blank=True, null=True)
    special_offers = models.TextField(blank=True, null=True, help_text="Special offers or discounts available for wheelers")
    facebook_url = models.URLField(blank=True, null=True, help_text="Facebook page URL")
    x_twitter_url = models.URLField(blank=True, null=True, help_text="X profile URL")
    instagram_url = models.URLField(blank=True, null=True, help_text="Instagram profile URL")
    pricing_tier = models.ForeignKey(
        PricingTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='businesses'
    )
    billing_frequency = models.CharField(
        max_length=10,
        choices=BILLING_FREQUENCY_CHOICES,
        default='monthly',
        help_text="Billing frequency for this business (monthly or yearly)"
    )
    wheeler_verification_requested = models.BooleanField(default=False)
    # Indicate if the business premises has been verified by Wheelers:
    verified_by_wheelers = models.BooleanField(default=False)
    # Indicate if the business is approved by the admin:
    is_approved = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String representation returns the business name."""
        return self.business_name


class WheelerVerification(models.Model):
    """
    Represents a verification of a business by a Wheeler (user).
    Links a business and a verifying user, with date and optional comments.
    Prevents duplicate verifications per business/user pair.
    """
    business = models.ForeignKey('Business', on_delete=models.CASCADE, related_name='verifications')
    wheeler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verifications_made')
    date_verified = models.DateTimeField(auto_now_add=True)
    comments = models.TextField()  # required comments field
    mobility_device = models.CharField(
        max_length=47,
        choices=getattr(settings, 'MOBILITY_DEVICE_CHOICES', (
            ('manual_wheelchair', 'Manual Wheelchair'),
            ('powered_wheelchair', 'Powered Wheelchair'),
            ('manual_wheelchair_with_powered_front_attachment', 'Manual Wheelchair with Powered Front Attachment'),
            ('all_terrain_wheelchair', 'All Terrain Wheelchair'),
            ('mobility_scooter_class_2', 'Mobility Scooter Class 2 (for footpaths)'),
            ('mobility_scooter_class_3', 'Mobility Scooter Class 3 (for road use)'),
            ('tricycle', 'Tricycle'),
            ('handcycle', 'Handcycle'),
            ('adapted_bicycle', 'Adapted Bicycle'),
            ('bicycle', 'Bicycle'),
            ('other', 'Other'),
        )),
        blank=True,
        null=True,
        help_text="Type of wheeled mobility device used during verification."
    )
    approved = models.BooleanField(default=False, help_text="Has this verification been approved by an admin?")
    # Store which features the wheeler confirmed
    confirmed_features = models.ManyToManyField(AccessibilityFeature, blank=False, related_name='confirmed_in_verifications')
    # Store any additional features the wheeler found
    additional_features = models.ManyToManyField(AccessibilityFeature, blank=True, related_name='additional_in_verifications')

    class Meta:
        unique_together = ('business', 'wheeler')  # prevent double verification

    def __str__(self):
        """String representation showing who verified which business and when."""
        return f"{self.wheeler} verified {self.business.business_name} on {self.date_verified.strftime('%Y-%m-%d')}"


class WheelerVerificationPhoto(models.Model):
    verification = models.ForeignKey(WheelerVerification, on_delete=models.CASCADE, related_name='photos')
    # Store verification photos under media/verification_photos
    image = models.ImageField(
        upload_to='verification_photos/',
        storage=MediaCloudinaryStorage(),
    )
    # Optional link to the specific accessibility feature this photo illustrates
    feature = models.ForeignKey(
        'AccessibilityFeature',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_photos'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        feat = self.feature.name if self.feature else 'General'
        return f"Photo ({feat}) for verification {self.verification.id} uploaded at {self.uploaded_at}" 


class WheelerVerificationRequest(models.Model):
    business = models.ForeignKey('Business', on_delete=models.CASCADE, related_name='verification_requests')
    wheeler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_requests_made')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)
    # Timestamp when the request was approved
    approved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # When flag approved is set, record the approval timestamp if not already set
        if self.approved and self.approved_at is None:
            from django.utils import timezone
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        status = 'Approved' if self.approved else 'Pending'
        return f"Request by {self.wheeler} for {self.business.business_name} ({status})"
