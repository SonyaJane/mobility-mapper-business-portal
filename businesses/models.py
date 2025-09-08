"""
Models for the businesses app, including MembershipTier, Business, and WheelerVerification.
Defines business tiers, business details, and accessibility/verification features.
"""

from django.contrib.gis.db import models as geomodels
from django.db import models
from django.utils.text import slugify
from core.validators import validate_logo
from django.conf import settings

TIER_CHOICES = [
    ('free', 'Free'),
    ('standard', 'Standard'),
    ('premium', 'Premium'),
]
    
class MembershipTier(models.Model):
    """
    Represents a membership tier for businesses.
    Includes annual membership, Stripe integration, tier type, and active status.
    """
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    description = models.JSONField()
    membership_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # Numeric price for a Wheeler verification when purchased separately
    verification_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # Note: Stripe Price IDs were removed from models; pricing is stored locally as
    # `membership_price` and `verification_price`. To reintroduce Stripe Price
    # references later, add fields and migrations.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_tier_display()


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
    Stores owner, details, location, accessibility, membership tier, and verification info.
    """
    class Meta:
        verbose_name_plural = "Businesses"
    # Owner is a UserProfile, which extends the User model
    business_owner = models.OneToOneField('accounts.UserProfile', on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = geomodels.PointField(geography=True)
    street_address1 = models.CharField(max_length=80, default='', blank=True)
    street_address2 = models.CharField(max_length=80, blank=True, null=True)
    town_or_city = models.CharField(max_length=40, default='', blank=True)
    county = models.CharField(max_length=80, blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    categories = models.ManyToManyField('Category', blank=True, related_name='businesses')
    accessibility_features = models.ManyToManyField('AccessibilityFeature', blank=True, related_name='businesses')
    logo = models.ImageField(
        upload_to='mobility_mapper_business_portal/business_logos/',
        blank=True,
        null=True,
        validators=[validate_logo],  # ensure model-level validation for logos
        error_messages={
            # Message used when Pillow/Django can't read the file (corrupted/unreadable)
            'invalid_image': 'The uploaded image appears corrupted or unreadable.'
        }
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
    membership_tier = models.ForeignKey(MembershipTier, on_delete=models.SET_NULL, null=True, blank=True, related_name='businesses')
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
    from accounts.models import MobilityDevice
    mobility_device = models.ForeignKey(
        MobilityDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verifications',
        help_text="Type of wheeled mobility device used during verification."
    )
    # Selfie of the Wheeler at the business
    selfie = models.ImageField(
        upload_to='mobility_mapper_business_portal/wheeler_selfies/',
    max_length=255,
    blank=True,
    null=True,
        help_text="A selfie of the Wheeler taken at the business."
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
    image = models.ImageField(
    upload_to='mobility_mapper_business_portal/verification_photos/',
    max_length=255,
    )
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

    class Meta:
        # Prevent duplicate requests for the same business/wheeler pair at the DB level
        unique_together = ('business', 'wheeler')
