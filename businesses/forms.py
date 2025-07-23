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
        widget=forms.SelectMultiple,
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
        # Group categories by group_description for the template
        categories = Category.objects.all().order_by('group_description', 'name')
        grouped = {}
        for cat in categories:
            group = cat.group_description or 'Other'
            grouped.setdefault(group, []).append((cat.code, cat.name))
        self.fields['categories'].choices = [(group, choices) for group, choices in grouped.items()]
        self.fields['accessibility_features'].queryset = AccessibilityFeature.objects.all()
        # Flat list for accessibility features multi-select
        features = AccessibilityFeature.objects.all()
        self.fields['accessibility_features'].choices = [(feat.code, feat.name) for feat in features]
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
        
