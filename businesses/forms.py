from django import forms
from .models import Business, WheelerVerification, PricingTier, BILLING_FREQUENCY_CHOICES
from .widgets import MapLibrePointWidget
from .models import AccessibilityFeature, Category
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.utils.safestring import mark_safe
from django.template.defaultfilters import slugify


class BusinessRegistrationForm(forms.ModelForm):
    public_phone = forms.CharField(
        required=False,
        label="Public phone number",
        help_text="This number will appear in search results so customers can call you directly."
    )
    contact_phone = forms.CharField(
        required=False,
        label="Contact phone number",
        help_text="This number will be used for internal communication only."
    )
    public_email = forms.EmailField(
        required=False,
        label="Public email address",
        help_text="This email will appear in search results so customers can contact you directly."
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
            'class': 'form-control auto-resize',  # ensure full-width styling
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
        label=mark_safe(
            "Business Categories*<br><small>Select the categories that describe your business. If yours isn't listed, choose 'Other' and enter it below.</small>"
        ),
        required=False
    )
    other_category = forms.CharField(
        required=False,
        label=mark_safe("Other Category*<br><small>If your category isn't listed, type it here and it will be added to our database.</small>"),
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter a new category here'})
    )
    accessibility_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.SelectMultiple,
        required=True,
        label="Select Accessibility Features"
    )
    location = forms.CharField(
        widget=MapLibrePointWidget(),
        label=mark_safe(
            "Business Location*<br><small>Find your business location on the map, zoom in for accuracy, and then click directly on your building or area to place a marker.</small>"
        ),
        required=True,
    )

    class Meta:
        model = Business
        fields = [
            'business_name',
            'address',
            'location',
            'public_phone',
            'contact_phone',
            'public_email',
            'website',
            'facebook_url',
            'x_twitter_url',
            'instagram_url',
            'categories',
            'other_category',
            'accessibility_features',
            'description',
            'services_offered',
            'special_offers',
            'opening_hours',
            'logo',
            'pricing_tier',
            'billing_frequency',
            ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # order categories by group and name so grouping works correctly
        self.fields['categories'].queryset = Category.objects.all().order_by('group_description', 'name')
        self.fields['accessibility_features'].queryset = AccessibilityFeature.objects.all()
        self.fields['pricing_tier'].queryset = PricingTier.objects.filter(is_active=True)
        self.fields['pricing_tier'].empty_label = "Select a pricing tier"
        try:
            free_tier = PricingTier.objects.filter(tier__iexact='Free', is_active=True).first()
            if free_tier:
                self.initial['pricing_tier'] = free_tier.pk
        except PricingTier.DoesNotExist:
            pass

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if not location:
            raise forms.ValidationError('This field is required.')
        return location

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            if isinstance(logo, (InMemoryUploadedFile, TemporaryUploadedFile)):
                image = Image.open(logo)
                if image.width != image.height:
                    raise forms.ValidationError("Logo must be square (width and height must be equal).")
        return logo

    def clean_categories(self):
        # Remove the special '__other__' marker from posted category values
        raw = self.data.getlist('categories') if hasattr(self.data, 'getlist') else self.data.get('categories', [])
        # Ensure we have a list
        if isinstance(raw, str):
            raw = [raw]
        selected_ids = [val for val in raw if val != '__other__']
        # Convert to Category instances
        categories = Category.objects.filter(pk__in=selected_ids)
        # If no real categories and no other_category provided, error
        other = self.data.get('other_category', '').strip()
        if not categories and not other:
            raise forms.ValidationError('Select at least one category or enter an Other category.')
        return categories

    def save(self, commit=True):
        # Save instance and m2m, then handle 'Other' category
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Save m2m relationships for categories and accessibility_features
            self.save_m2m()
            # Handle 'Other' entry by adding new Category
            other_cat = self.cleaned_data.get('other_category')
            if other_cat:
                slug = slugify(other_cat)
                category, created = Category.objects.get_or_create(
                    code=slug,
                    defaults={'name': other_cat}
                )
                instance.categories.add(category)
        return instance


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

