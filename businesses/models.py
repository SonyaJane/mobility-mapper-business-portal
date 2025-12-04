"""
Models for the businesses app, including MembershipTier, Business, and WheelerVerification.
Defines business tiers, business details, and accessibility/verification features.
"""

from django.contrib.gis.db import models as geomodels
from django.db import models
from core.validators import validate_logo

TIER_CHOICES = [
    ('free', 'Free'),
    ('standard', 'Standard'),
    ('premium', 'Premium'),
]


class MembershipTier(models.Model):
    """
    Represents a membership tier for businesses, including tier type (free, standard or premium),
    annual membership price, and verification price.
    """
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    description = models.JSONField()
    membership_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    verification_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
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
    """
    class Meta:
        verbose_name_plural = "Businesses"
    # Owner is a UserProfile, which links to the User model
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
        null=True
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
    verified_by_wheelers = models.BooleanField(default=False)
    # Indicate if the business is approved by the admin:
    is_approved = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String representation returns the business name."""
        return self.business_name

