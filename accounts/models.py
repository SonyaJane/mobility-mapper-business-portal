from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """User profile model to extend the User model with additional fields."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_wheeler = models.BooleanField(default=False)
    has_business = models.BooleanField(default=False)

    def __str__(self):
            return self.user.username

# Automatically create/update UserProfile when User is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
