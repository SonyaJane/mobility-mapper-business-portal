from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class County(models.Model):
    """
    Represents a UK county for user profiles.
    """
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

class AgeGroup(models.Model):
    """
    Represents an age group for user profiles.
    """
    code = models.CharField(max_length=16, unique=True)
    description = models.CharField(max_length=50)

    def __str__(self):
        return self.description

class MobilityDevice(models.Model):
    """
    Represents a mobility device type for Wheelers and verifications.
    """
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    COUNTRY_CHOICES = (
        ("UK", "United Kingdom"),
        ("Other", "Other"),
    )
    country = models.CharField(
        max_length=32,
        choices=COUNTRY_CHOICES,
        default="UK",
        help_text="Country of residence."
    )
    county = models.ForeignKey(
        County,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="County of residence"
    )
    """User profile model to extend the User model with additional fields."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(
        upload_to='mobility_mapper_business_portal/profile_photos/',
        blank=True,
        null=True,
    )
    is_wheeler = models.BooleanField(default=False)
    has_business = models.BooleanField(default=False)
    has_registered_business = models.BooleanField(
        default=False,
        help_text="Whether the user has registered their business on the site."
    )

    # Allow multiple mobility devices
    mobility_devices = models.ManyToManyField(
        MobilityDevice,
        blank=True,
        help_text="Types of wheeled mobility devices (if user is a wheeler)."
    )
    mobility_devices_other = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Other mobility device description (if 'Other' selected)."
    )

    # Age group is now a ForeignKey to AgeGroup model
    age_group = models.ForeignKey(
        AgeGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

# Automatically create/update UserProfile when User is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Skip auto-creation when loading fixtures (raw=True)
    if kwargs.get('raw', False):
        return
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
