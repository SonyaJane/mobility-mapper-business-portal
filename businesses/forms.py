from django import forms
from .models import Business, WheelerVerification, PricingTier, BILLING_FREQUENCY_CHOICES
from .widgets import MapLibrePointWidget

class BusinessRegistrationForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.SelectMultiple,
        required=False,
        label="Business Categories"
    )
    billing_frequency = forms.ChoiceField(
        choices=BILLING_FREQUENCY_CHOICES,
        widget=forms.RadioSelect,
        initial='monthly',
        label="Billing Option"
    )
    accessibility_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Business
        exclude = [
            'business_owner',
            'wheeler_verification_requested',
            'verified_by_wheelers',
            'wheeler_verification_notes',
            'is_approved',
        ]
        widgets = {
            'location': MapLibrePointWidget(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import AccessibilityFeature, Category
        self.fields['categories'].queryset = Category.objects.all()
        self.fields['accessibility_features'].queryset = AccessibilityFeature.objects.all()
        self.fields['pricing_tier'].queryset = PricingTier.objects.filter(is_active=True)
        self.fields['pricing_tier'].empty_label = "Select a pricing tier"
        if not self.initial.get('billing_frequency'):
            self.initial['billing_frequency'] = 'monthly'
        try:
            free_tier = PricingTier.objects.filter(tier__iexact='Free', is_active=True).first()
            if free_tier:
                self.initial['pricing_tier'] = free_tier.pk
        except PricingTier.DoesNotExist:
            pass
        



class WheelerVerificationForm(forms.ModelForm):
    class Meta:
        model = WheelerVerification
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }
        
