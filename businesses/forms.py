from django import forms
from .models import Business, WheelerVerification, PricingTier, BILLING_FREQUENCY_CHOICES
from .widgets import MapLibrePointWidget

class BusinessRegistrationForm(forms.ModelForm):
    categories = forms.MultipleChoiceField(
        choices=[],  # Will be set in __init__
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

    accessibility_features = forms.MultipleChoiceField(
        choices=[],  # Will be set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Business
        exclude = [
            'owner',
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

        # Limit pricing tier choices to active tiers
        self.fields['pricing_tier'].queryset = PricingTier.objects.filter(is_active=True)
        self.fields['pricing_tier'].empty_label = "Select a pricing tier"

        # Dynamically set accessibility feature choices from the model
        from .models import AccessibilityFeature, Category
        self.fields['accessibility_features'].choices = [
            (feature.code, feature.name)
            for feature in AccessibilityFeature.objects.all()
        ]
        # Group categories by group_description
        from collections import defaultdict
        grouped = defaultdict(list)
        for cat in Category.objects.all():
            group_label = cat.group_description or "Other"
            grouped[group_label].append((cat.code, cat.name))
        self.fields['categories'].choices = [
            (group, choices) for group, choices in grouped.items()
        ]

        # Auto select monthly billing frequency
        if not self.initial.get('billing_frequency'):
            self.initial['billing_frequency'] = 'monthly'

        # Auto-select the 'Free' tier if available
        try:
            free_tier = PricingTier.objects.filter(tier__iexact='Free', is_active=True).first()
            if free_tier:
                self.initial['pricing_tier'] = free_tier.pk
        except PricingTier.DoesNotExist:
            pass
        
    def clean_accessibility_features(self):
        # Store the list as JSON
        data = self.cleaned_data['accessibility_features']
        return list(data)


class WheelerVerificationForm(forms.ModelForm):
    class Meta:
        model = WheelerVerification
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }
        
