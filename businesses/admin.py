from django import forms
from django.contrib import admin
from .models import Business, MembershipTier, Category, AccessibilityFeature
from core.widgets import MapLibrePointWidget
from verification.admin import WheelerVerificationInline

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
    list_display = ('business_name', 'business_owner', 'membership_tier', 'is_approved', 'wheeler_verification_count')
    list_filter = ('membership_tier', 'is_approved', 'verified_by_wheelers', 'categories', 'accessibility_features')
    search_fields = ('business_name', 'business_owner__email')
    inlines = [WheelerVerificationInline]
    filter_horizontal = ('categories', 'accessibility_features')

    # Display count of Wheeler verifications
    def wheeler_verification_count(self, obj):
        return obj.verifications.count()
    wheeler_verification_count.short_description = "Wheeler Verifications"


@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ("tier", "is_active")
    list_filter = ("is_active",)
    search_fields = ("tier",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'group_code', 'group_description', 'tags')
    search_fields = ('code', 'name')
    list_filter = ('group_code',)


@admin.register(AccessibilityFeature)
class AccessibilityFeatureAdmin(admin.ModelAdmin):
    list_display = ('code','name')

