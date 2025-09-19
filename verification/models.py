"""
Models for the verification app
"""

from django.conf import settings
from django.db import models
from businesses.models import AccessibilityFeature 
from accounts.models import MobilityDevice

class WheelerVerification(models.Model):
    """
    Represents a verification of a business by a Wheeler (user).
    Links a business and a verifying user, with date and optional comments.
    Prevents duplicate verifications per business/user pair.
    """
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='verifications')
    wheeler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verifications_made')
    date_verified = models.DateTimeField(auto_now_add=True)
    comments = models.TextField()
    mobility_device = models.ForeignKey(
        MobilityDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verifications',
        help_text="Type of wheeled mobility device used during verification."
    )
    selfie = models.ImageField(
        upload_to='mobility_mapper_business_portal/wheeler_selfies/',
        help_text="A selfie of the Wheeler taken at the business.",
        max_length=255,
        null=True,
        blank=True 
    )
    approved = models.BooleanField(default=False, help_text="Has this verification been approved by an admin?")
    # features the wheeler confirmed
    confirmed_features = models.ManyToManyField(AccessibilityFeature, blank=False, related_name='confirmed_in_verifications')
    # additional features the wheeler found
    additional_features = models.ManyToManyField(AccessibilityFeature, blank=True, related_name='additional_in_verifications')

    class Meta:
        unique_together = ('business', 'wheeler')  # prevent double verification

    def __str__(self):
        """String representation showing who verified which business and when."""
        return f"{self.wheeler} verified {self.business.business_name} on {self.date_verified.strftime('%Y-%m-%d')}"


class WheelerVerificationPhoto(models.Model):
    """Represents a photo submitted by a Wheeler during the verification process.
    Each photo is linked to a specific verification and to an accessibility feature.
    """
    verification = models.ForeignKey(WheelerVerification, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(
        upload_to='mobility_mapper_business_portal/verification_photos/',
        max_length=255,
    )
    feature = models.ForeignKey(
        'businesses.AccessibilityFeature',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_photos'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        feat = self.feature.name if self.feature else 'General'
        return f"Photo ({feat}) for verification {self.verification.id} uploaded at {self.uploaded_at}" 


class WheelerVerificationApplication(models.Model):
    """Tracks applications by wheelers to verify a business's accessibility."""
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='verification_requests')
    wheeler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_requests_made')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
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
