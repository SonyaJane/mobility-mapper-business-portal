from django.contrib import admin
from .models import WheelerVerification, WheelerVerificationApplication, WheelerVerificationPhoto
from django.core.mail import send_mail
from django.conf import settings


@admin.register(WheelerVerification)
class WheelerVerificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the WheelerVerification model.
    Displays verification details, allows approval, and shows related features and photos.
    """
    list_display = ('business', 'wheeler', 'date_verified', 'comments', 'mobility_device', 'approved', 'get_confirmed_features', 'get_additional_features')
    search_fields = ('business__name', 'wheeler__email')
    list_filter = ('date_verified', 'approved')
    actions = ['approve_verifications']


    class WheelerVerificationPhotoInline(admin.TabularInline):
        """
        Inline admin for WheelerVerificationPhoto.
        Displays photo previews and allows editing related to a verification.
        """
        model = WheelerVerificationPhoto
        fk_name = 'verification'
        extra = 0
        readonly_fields = ('image_preview',)
        fields = ('image_preview', 'image', 'feature')

        def image_preview(self, obj):
            """
            Returns an HTML image preview for the admin inline.
            """
            from django.utils.html import format_html
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image)
        image_preview.short_description = 'Preview'

    def approve_verifications(self, request, queryset):
        """
        Admin action to mark selected verifications as approved.
        """
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} verification(s) marked as approved.")
    approve_verifications.short_description = "Approve selected verifications"

    def get_confirmed_features(self, obj):
        """
        Returns a comma-separated list of confirmed features for the verification.
        """
        return ", ".join([f.name for f in obj.confirmed_features.all()])
    get_confirmed_features.short_description = 'Confirmed features'

    def get_additional_features(self, obj):
        """
        Returns a comma-separated list of additional features for the verification.
        """
        return ", ".join([f.name for f in obj.additional_features.all()])
    get_additional_features.short_description = 'Additional features'


class WheelerVerificationInline(admin.TabularInline):
    """
    Inline admin for WheelerVerification.
    Allows editing verifications directly from the related business admin page.
    """
    model = WheelerVerification
    extra = 0  # no blank entries by default


@admin.register(WheelerVerificationApplication)
class WheelerVerificationApplicationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the WheelerVerificationApplication model.
    Handles approval, notification emails, and displays application details.
    """
    def save_model(self, request, obj, form, change):
        """
        Sends an approval email to the wheeler if the application is approved.
        """
        # Only send email if approval status changed to True
        send_email = False
        if change:
            old_obj = WheelerVerificationApplication.objects.get(pk=obj.pk)
            if not old_obj.approved and obj.approved:
                send_email = True
        elif obj.approved:
            send_email = True
        super().save_model(request, obj, form, change)
        if send_email and obj.wheeler.email:
            from django.urls import reverse
            verification_url = settings.SITE_URL + reverse('wheeler_verification_form', args=[obj.business.pk])
            send_mail(
                subject="Your application has been approved",
                message=(
                    f"Hi {obj.wheeler.get_full_name() or obj.wheeler.username},\n\n"
                    f"Your application to verify accessibility features for {obj.business.business_name} has been approved.\n\n"
                    f"You may now proceed with the verification process by visiting the following link:\n{verification_url}\n\n"
                    f"You can also access the verification form from your dashboard. Look for the 'Submit Verification' button next to the business.\n\n"
                    f"Thank you!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.wheeler.email],
                fail_silently=True,
            )
    list_display = ('business', 'wheeler', 'requested_at', 'approved_at', 'approved')
    readonly_fields = ('approved_at',)
    list_filter = ('approved', 'business')
    search_fields = ('business__business_name', 'wheeler__username')
    actions = ['approve_requests']

    def approve_requests(self, request, queryset):
        """
        Admin action to approve selected verification requests and notify users by email.
        """
        for req in queryset:
            if not req.approved:
                req.approved = True
                req.reviewed = True
                req.save()
                # Send notification email to the wheeler
                if req.wheeler.email:
                    from django.urls import reverse
                    verification_url = settings.SITE_URL + reverse('wheeler_verification_form', args=[req.business.pk])
                    send_mail(
                        subject="Your verification request has been approved",
                        message=(
                            f"Hi {req.wheeler.get_full_name() or req.wheeler.username},\n\n"
                            f"Your request to verify accessibility features for {req.business.business_name} has been approved.\n\n"
                            f"You may now proceed with the verification process by visiting the following link:\n{verification_url}\n\n"
                            f"You can also access the verification form from your dashboard. Look for the 'Submit Verification' button next to the business.\n\n"
                            f"Thank you!"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[req.wheeler.email],
                        fail_silently=True,
                    )
        self.message_user(request, f"{queryset.count()} request(s) approved and users notified.")
    approve_requests.short_description = "Approve selected requests and notify users"


@admin.register(WheelerVerificationPhoto)
class WheelerVerificationPhotoAdmin(admin.ModelAdmin):
    """
    Admin configuration for the WheelerVerificationPhoto model.
    Displays photo details and allows filtering and searching by feature or business.
    """
    list_display = ('verification', 'feature', 'image', 'uploaded_at')
    list_filter = ('feature',)
    search_fields = ('verification__business__business_name',)
