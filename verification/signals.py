from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import WheelerVerification

# Store the old value before saving
@receiver(pre_save, sender=WheelerVerification)
def store_old_approved(sender, instance, **kwargs):
    if instance.pk and sender.objects.filter(pk=instance.pk).exists():
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
            
            # Email to business for nth verification
            verification_count = WheelerVerification.objects.filter(
                business=instance.business, approved=True
            ).count()
            suffix = (
                'st' if verification_count == 1 else
                'nd' if verification_count == 2 else
                'rd' if verification_count == 3 else
                'th'
            )
            biz_subject = f"Your business has received its {verification_count}{suffix} accessibility verification!"
            biz_message = (
                f"Dear {instance.business.owner.get_full_name() or instance.business.owner.username},\n\n"
                f"Your business, {instance.business.business_name}, has just received its {verification_count} accessibility verification from a user of a wheeled mobility device.\n"
                "You can view all verification reports in your business dashboard.\n\n"
            )
            # Add badge info if it's the 3rd verification
            if verification_count == 3:
                biz_message += (
                    "Since this is the 3rd verification, your business has now been awarded the Verified by Wheelers badge. "
                    "This badge is visible on your business dashboard and in the business search results.\n\n"
                )
            biz_message += (
                "Thank you for supporting accessibility in your community!\n"
                "Best regards,\n"
                "The Mobility Mapper Team"
            )
            print(f"Sending verification count email to {instance.business.owner.email}")
            send_mail(
                biz_subject,
                biz_message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.business.owner.email],
                fail_silently=False,
            )