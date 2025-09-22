from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import WheelerVerification

@receiver(post_save, sender=WheelerVerification)
def send_approval_email(sender, instance, created, **kwargs):
    # Only send if not just created, and approved is now True, and was previously False
    if not created:
        # Get the previous value from the database
        old = sender.objects.get(pk=instance.pk)
        if not old.approved and instance.approved:
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
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.wheeler.email],
                fail_silently=False,
            )