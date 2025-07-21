from django import forms
from django.contrib import admin
from .models import Business, WheelerVerification, PricingTier, Category, AccessibilityFeature
from .widgets import MapLibrePointWidget

@admin.register(WheelerVerification)
class WheelerVerificationAdmin(admin.ModelAdmin):
    list_display = ('business', 'wheeler', 'date_verified')
    search_fields = ('business__name', 'wheeler__email')
    list_filter = ('date_verified',)

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

    def wheeler_verification_count(self, obj):
        return obj.verifications.count()

    wheeler_verification_count.short_description = "Wheeler Verifications"


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ("tier", "price_per_month", "is_active")
    list_filter = ("is_active",)
    search_fields = ("tier",)
