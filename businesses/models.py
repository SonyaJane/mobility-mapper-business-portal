from django.contrib.gis.db import models as geomodels
from django.db import models
from django.conf import settings
    
class PricingTier(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    price_per_month = models.DecimalField(max_digits=6, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, help_text="The Stripe Price ID for this tier")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (£{self.price_per_month}/mo)"


TIER_CHOICES = [
    ('free', 'Free'),
    ('supporter', 'Supporter'),
    ('featured', 'Featured'),
]

CATEGORY_CHOICES = [
    ('cafe', 'Café'),
    ('retail', 'Retail Store'),
    ('gym', 'Gym'),
    ('hotel', 'Hotel'),
    ('healthcare', 'Healthcare'),
    ('other', 'Other'),
]

ACCESSIBILITY_FEATURE_CHOICES = [
    ('step_free', 'Step-free access'),
    ('wide_doors', 'Wide doors'),
    ('accessible_toilet', 'Accessible toilet'),
    ('hearing_loop', 'Hearing loop'),
    ('assistance_available', 'Staff assistance available'),
    ('low_counter', 'Low counter'),
    ('disabled_parking', 'Disabled parking'),
]

class Business(models.Model):
    owner = models.OneToOneField('accounts.UserProfile', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = geomodels.PointField(geography=True)  # Requires PostGIS
    address = models.CharField(max_length=300)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    accessibility_features = models.JSONField(default=list, blank=True)
    pricing_tier = models.ForeignKey(
        PricingTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='businesses'
    )
    wheeler_verification_requested = models.BooleanField(default=False)
    verified_by_wheelers = models.BooleanField(default=False) # Indicates if the business premises has been verified by Wheelers
    wheeler_verification_notes = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False) # Indicates if the business is approved by the admin
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def is_free(self):
        return self.tier == 'free'

    def is_supporter(self):
        return self.tier == 'supporter'

    def is_featured(self):
        return self.tier == 'featured'

    def has_feature(self, feature_name):
        """
        Tier-based feature access
        """
        tier_features = {
            'free': [
                'basic_listing', 
                'category', 
                'address'
                ],
            'supporter': [
                'basic_listing',
                'category',
                'address',
                'logo',
                'website',
                'opening_hours',
                'description',
            ],
            'featured': [
                'basic_listing',
                'category',
                'address',
                'logo',
                'website',
                'opening_hours',
                'description',
                'highlighted',
                'priority_sort',
            ],
        }

        return feature_name in tier_features.get(self.tier, [])
    
    @property
    def is_wheeler_verified(self):
        return self.verifications.exists()
    

class WheelerVerification(models.Model):
    business = models.ForeignKey('Business', on_delete=models.CASCADE, related_name='verifications')
    wheeler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verifications_made')
    date_verified = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('business', 'wheeler')  # prevent double verification

    def __str__(self):
        return f"{self.wheeler} verified {self.business.name} on {self.date_verified.strftime('%Y-%m-%d')}"
    
    

