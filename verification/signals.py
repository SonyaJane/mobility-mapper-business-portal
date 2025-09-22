from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import WheelerVerification

# Store the old value before saving
@receiver(pre_save, sender=WheelerVerification)
def store_old_approved(sender, instance, **kwargs):
    if instance.pk:
        old = sender.objects.get(pk=instance.pk)
        instance._old_approved = old.approved
    else:
        instance._old_approved = False

@receiver(post_save, sender=WheelerVerification)
def send_approval_email(sender, instance, created, **kwargs):
    print(f"Post-save signal received for WheelerVerification id={instance.id}, created={created}")
    # Only send if not just created, and approved changed from False to True
    if not created and hasattr(instance, '_old_approved'):
        if not instance._old_approved and instance.approved:
            subject = f"Your verification for {instance.business.business_name} has been approved!"
            message = (
                f"Dear {instance.wheeler.get_full_name() or instance.wheeler.username},\n"
                f"Congratulations! Your accessibility verification for {instance.business.business_name} has been approved.\n"
                f"You can view the verification report on the Accessibility Verification Hub.\n"
                f"You will soon receive a £10 Amazon gift card as a token of appreciation.\n"
                "Thank you for helping make our community more accessible!\n"
                "Best regards,\n"
                "The Mobility Mapper Team"
            )
            print(f"Sending approval email to {instance.wheeler.email}")
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.wheeler.email],
                fail_silently=False,
            )