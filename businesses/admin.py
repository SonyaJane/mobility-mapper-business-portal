"""
Admin configuration for the businesses app.

- Customises the admin interface for Business, MembershipTier, Category, and AccessibilityFeature models.
- Integrates a custom map widget for business location.
- Provides inline editing for WheelerVerifications on the Business admin page.
"""

from core.widgets import MapLibrePointWidget
from django import forms
from django.contrib import admin
from .models import Business, MembershipTier, Category, AccessibilityFeature
from verification.admin import WheelerVerificationInline


class BusinessAdminForm(forms.ModelForm):
    """
    Custom form for the Business admin interface.
    Uses a custom map widget for the location field and sets querysets for categories and accessibility features.
    """
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
    """
    Admin configuration for the Business model.
    - Uses a custom form with a map widget.
    - Displays key business fields and a count of Wheeler verifications.
    - Allows inline editing of related WheelerVerifications.
    """
    form = BusinessAdminForm
    list_display = ('business_name', 'business_owner', 'membership_tier', 'is_approved', 'wheeler_verification_count')
    list_filter = ('membership_tier', 'is_approved', 'verified_by_wheelers', 'categories', 'accessibility_features')
    search_fields = ('business_name', 'business_owner__email')
    inlines = [WheelerVerificationInline]
    filter_horizontal = ('categories', 'accessibility_features')

    # Display count of Wheeler verifications
    def wheeler_verification_count(self, obj):
        """
        Returns the number of Wheeler verifications for the business.
        """
        return obj.verifications.count()
    wheeler_verification_count.short_description = "Wheeler Verifications"


@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    """
    Admin configuration for the MembershipTier model.
    Displays tier and active status, and allows filtering and searching.
    """
    list_display = ("tier", "is_active")
    list_filter = ("is_active",)
    search_fields = ("tier",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    Displays code, name, group, and tags, and allows filtering and searching.
    """
    list_display = ('code', 'name', 'group_code', 'group_description', 'tags')
    search_fields = ('code', 'name')
    list_filter = ('group_code',)


@admin.register(AccessibilityFeature)
class AccessibilityFeatureAdmin(admin.ModelAdmin):
    """
    Admin configuration for the AccessibilityFeature model.
    Displays code and name.
    """
    list_display = ('code', 'name')
