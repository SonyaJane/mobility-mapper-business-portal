from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class AgeGroup(models.Model):
    """
    Represents an age group for user profiles.
    """
    name = models.CharField(max_length=16, unique=True)
    label = models.CharField(max_length=50)

    def __str__(self):
        """
        Return the display label for the age group.
        """
        return self.label


class County(models.Model):
    """
    Represents a UK county for user profiles.
    """
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)

    def __str__(self):
        """
        Return the display label for the county.
        """
        return self.label

class MobilityDevice(models.Model):
    """
    Represents a mobility device type for Wheelers and verifications.
    """
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)

    def __str__(self):
        """
        Return the display label for the mobility device.
        """
        return self.label

class UserProfile(models.Model):
    """
    Extends the User model with additional profile fields such as country, county,
    photo, mobility device information, age group, and business-related flags.
    """
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
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
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
        """
        Return the username associated with this profile.
        """
        return self.user.username

@receiver(post_save, sender=get_user_model())
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver to automatically create or update a UserProfile
    whenever a User instance is created or saved.
    Skips auto-creation when loading fixtures (raw=True).
    """
    # Skip auto-creation when loading fixtures (raw=True)
    if kwargs.get('raw', False):
        return
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Try to save existing profile; if missing, create it.
        try:
            # use related_name 'profile' for the reverse accessor
            instance.profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)
