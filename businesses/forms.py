from django import forms
from .models import Business, WheelerVerification, PricingTier, BILLING_FREQUENCY_CHOICES
from .widgets import MapLibrePointWidget
from .models import AccessibilityFeature, Category
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile


class BusinessRegistrationForm(forms.ModelForm):
    public_phone = forms.CharField(
        required=False,
        label="Public phone number"
    )
    contact_phone = forms.CharField(
        required=False,
        label="Contact phone number"
    )
    public_email = forms.EmailField(
        required=False,
        label="Public email address"
    )
    services_offered = forms.CharField(
        required=False,
        label="Services offered",
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe the services your business offers, e.g. delivery, in-store shopping, etc.',
            'class': 'auto-resize',
            'rows': 3
        })
    )
    description = forms.CharField(
        required=False,
        label="Business description",
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe your business, what makes it unique, and any important details for customers.',
            'class': 'auto-resize',
            'rows': 3
        })
    )

    opening_hours = forms.CharField(
        required=False,
        label="Business Hours",
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g. Mon-Fri 9am-5pm; Sat 10am-2pm; Sun closed',
            'class': 'auto-resize',
            'rows': 3
        })
    )

    special_offers = forms.CharField(
        required=False,
        label="Special Offers",
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe any special offers or discounts for wheelers.',
            'class': 'auto-resize',
            'rows': 3
        })
    )
    facebook_url = forms.URLField(
        required=False,
        label="Facebook Page URL"
    )
    x_twitter_url = forms.URLField(
        required=False,
        label="X (formerly Twitter) Profile URL"
    )
    instagram_url = forms.URLField(
        required=False,
        label="Instagram Profile URL"
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.SelectMultiple,
        required=False,
        label="Select Business Categories"
    )
    accessibility_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.SelectMultiple,
        required=False,
        label="Select Accessibility Features"
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
        self.fields['categories'].queryset = Category.objects.all()
        self.fields['accessibility_features'].queryset = AccessibilityFeature.objects.all()
        self.fields['pricing_tier'].queryset = PricingTier.objects.filter(is_active=True)
        self.fields['pricing_tier'].empty_label = "Select a pricing tier"
        try:
            free_tier = PricingTier.objects.filter(tier__iexact='Free', is_active=True).first()
            if free_tier:
                self.initial['pricing_tier'] = free_tier.pk
        except PricingTier.DoesNotExist:
            pass
    
        
    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            if isinstance(logo, (InMemoryUploadedFile, TemporaryUploadedFile)):
                image = Image.open(logo)
                if image.width != image.height:
                    raise forms.ValidationError("Logo must be square (width and height must be equal).")
        return logo
        

class WheelerVerificationForm(forms.ModelForm):

    confirmed_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Accessibility features you have confirmed at this business"
    )
    additional_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.SelectMultiple,
        required=False,
        label="Additional accessibility features you found (select any that apply)"
    )

    class Meta:
        model = WheelerVerification
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write a brief report about your visit and the features you verified.'}),
        }

    def __init__(self, *args, **kwargs):
        business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        from .models import AccessibilityFeature
        self.fields['confirmed_features'].queryset = AccessibilityFeature.objects.none()
        if business:
            self.fields['confirmed_features'].queryset = business.accessibility_features.all()
        self.fields['additional_features'].queryset = AccessibilityFeature.objects.all()
        
