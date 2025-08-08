from django import forms
from django.contrib import admin
from .models import Business, WheelerVerification, PricingTier, Category, AccessibilityFeature
from .widgets import MapLibrePointWidget
from .models import WheelerVerificationRequest
from django.core.mail import send_mail
from django.conf import settings

@admin.register(WheelerVerification)
class WheelerVerificationAdmin(admin.ModelAdmin):
    list_display = ('business', 'wheeler', 'date_verified', 'approved')
    search_fields = ('business__name', 'wheeler__email')
    list_filter = ('date_verified', 'approved')
    actions = ['approve_verifications']

    def approve_verifications(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} verification(s) marked as approved.")
    approve_verifications.short_description = "Approve selected verifications"

class WheelerVerificationInline(admin.TabularInline):
    model = WheelerVerification
    extra = 0  # no blank entries by default
    
    
class BusinessAdminForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = '__all__'
        widgets = {
            'location': MapLibrePointWidget(),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices for categories and accessibility_features
        self.fields['categories'].queryset = Category.objects.all()
        self.fields['accessibility_features'].queryset = AccessibilityFeature.objects.all()
        
        
@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    form = BusinessAdminForm
    list_display = ('business_name', 'business_owner', 'pricing_tier', 'is_approved', 'wheeler_verification_count')
    list_filter = ('pricing_tier', 'is_approved', 'verified_by_wheelers', 'categories', 'accessibility_features')
    search_fields = ('business_name', 'business_owner__email')
    inlines = [WheelerVerificationInline]

    # Display count of Wheeler verifications
    def wheeler_verification_count(self, obj):
        return obj.verifications.count()
    wheeler_verification_count.short_description = "Wheeler Verifications"


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ("tier", "price_per_month", "is_active")
    list_filter = ("is_active",)
    search_fields = ("tier",)


@admin.register(WheelerVerificationRequest)
class WheelerVerificationRequestAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # Only send email if approval status changed to True
        send_email = False
        if change:
            old_obj = WheelerVerificationRequest.objects.get(pk=obj.pk)
            if not old_obj.approved and obj.approved:
                send_email = True
        elif obj.approved:
            send_email = True
        super().save_model(request, obj, form, change)
        if send_email and obj.wheeler.email:
            from django.urls import reverse
            verification_url = settings.SITE_URL + reverse('submit_verification', args=[obj.business.pk])
            send_mail(
                subject="Your verification request has been approved",
                message=(
                    f"Hi {obj.wheeler.get_full_name() or obj.wheeler.username},\n\n"
                    f"Your request to verify accessibility features for {obj.business.business_name} has been approved.\n\n"
                    f"You may now proceed with the verification process by visiting the following link:\n{verification_url}\n\n"
                    f"You can also access the verification form from your dashboard. Look for the 'Submit Verification' button next to the business.\n\n"
                    f"Thank you!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.wheeler.email],
                fail_silently=True,
            )
    list_display = ('business', 'wheeler', 'requested_at', 'approved', 'reviewed')
    list_filter = ('approved', 'reviewed', 'business')
    search_fields = ('business__business_name', 'wheeler__username')
    actions = ['approve_requests']

    def approve_requests(self, request, queryset):
        for req in queryset:
            if not req.approved:
                req.approved = True
                req.reviewed = True
                req.save()
                # Send notification email to the wheeler
                if req.wheeler.email:
                    from django.urls import reverse
                    verification_url = settings.SITE_URL + reverse('submit_verification', args=[req.business.pk])
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
