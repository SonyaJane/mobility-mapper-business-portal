from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     """Create a UserProfile instance when a User is created."""
#     if created:
#         UserProfile.objects.create(user=instance)
