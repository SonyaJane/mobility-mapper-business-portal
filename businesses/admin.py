from django import forms
from django.contrib import admin
from .models import Business, WheelerVerification, PricingTier, Category, AccessibilityFeature, WheelerVerificationPhoto
from .widgets import MapLibrePointWidget
from .models import WheelerVerificationRequest
from django.core.mail import send_mail
from django.conf import settings

@admin.register(WheelerVerification)
class WheelerVerificationAdmin(admin.ModelAdmin):
    list_display = ('business', 'wheeler', 'date_verified', 'comments', 'mobility_device', 'approved')
    search_fields = ('business__name', 'wheeler__email')
    list_filter = ('date_verified', 'approved')
    actions = ['approve_verifications']
    # Inline photos for each verification
    # Inline display of verification photos
    class WheelerVerificationPhotoInline(admin.TabularInline):
        model = WheelerVerificationPhoto
        fk_name = 'verification'
        extra = 0
        readonly_fields = ('image_preview',)
        fields = ('image_preview', 'image', 'feature')
        def image_preview(self, obj):
            from django.utils.html import format_html
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        image_preview.short_description = 'Preview'

    inlines = [WheelerVerificationPhotoInline]

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
    filter_horizontal = ('categories', 'accessibility_features')

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
            verification_url = settings.SITE_URL + reverse('wheeler_verification_form', args=[obj.business.pk])
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
    list_display = ('business', 'wheeler', 'requested_at', 'approved_at', 'approved', 'reviewed')
    readonly_fields = ('approved_at',)
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
    list_display = ('verification', 'feature', 'image', 'uploaded_at')
    list_filter = ('feature',)
    search_fields = ('verification__business__business_name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'group_code', 'group_description', 'tags')
    search_fields = ('code', 'name')
    list_filter = ('group_code',)


@admin.register(AccessibilityFeature)
class AccessibilityFeatureAdmin(admin.ModelAdmin):
    list_display = ('code','name')

