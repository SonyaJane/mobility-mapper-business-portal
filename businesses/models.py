from django.contrib.gis.db import models as geomodels
from django.db import models
from django.conf import settings

TIER_CHOICES = [
    ('free', 'Free'),
    ('supporter', 'Supporter'),
    ('featured', 'Featured'),
    ('partner', 'Premier Partner'),
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
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = geomodels.PointField(geography=True)  # Requires PostGIS
    address = models.CharField(max_length=300)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    accessibility_features = models.JSONField(default=list, blank=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
