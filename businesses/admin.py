from django import forms
from django.contrib import admin
from .models import Business, WheelerVerification
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
            'location': MapLibrePointWidget(),  # Use your custom map widget here
        }    
        
        
@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    form = BusinessAdminForm
    list_display = ('name', 'owner', 'tier', 'category', 'is_approved', 'wheeler_verification_count')
    list_filter = ('tier', 'category', 'is_approved', 'verified_by_wheelers')
    search_fields = ('name', 'owner__email')
    inlines = [WheelerVerificationInline]
    
    def wheeler_verification_count(self, obj):
        return obj.verifications.count()

    wheeler_verification_count.short_description = "Wheeler Verifications"

