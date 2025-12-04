"""
Forms for the businesses app.

- BusinessRegistrationForm: Handles business registration with custom validation and widget logic.
- BusinessUpdateForm: Handles business updates, omitting membership tier and supporting logo removal.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import Business, MembershipTier, AccessibilityFeature, Category
from core.widgets import MapLibrePointWidget
from core.validators import validate_logo


class BusinessRegistrationForm(forms.ModelForm):
    """
    Form for registering a new business.

    - Provides custom widgets and help text for business fields.
    - Validates and parses location input as a GEOS Point.
    - Validates uploaded logo file type and delegates further checks to a centralised validator.
    """
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
            'class': 'auto-resize',
            'rows': 3
        })
    )
    special_offers = forms.CharField(
        required=False,
        label="Special Offers",
        widget=forms.Textarea(attrs={
            'placeholder': 'Add any discounts or promotions specifically for Wheelers to encourage customers to come to your business.',
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
        label="Business Categories*",
        help_text="Select the categories that describe your business.",
        required=False
    )
    accessibility_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.SelectMultiple,
        required=True,
        label="Select Accessibility Features"
    )
    location = forms.CharField(
        widget=MapLibrePointWidget(),
        label="Business Location",
        help_text="Find your business location on the map, zoom in for accuracy, and then click directly on your building or area to place a marker.",
        required=True,
    )
    # Use FileField so we can validate extension/MIME first in clean_logo
    logo = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
        label='Business Logo',
        help_text='The image must be in PNG, JPEG, or WEBP format, square, and no larger than 5MB.',
        required=False,
    )

    class Meta:
        model = Business
        fields = [
            'business_name',
            'street_address1', 'street_address2', 'town_or_city', 'county', 'postcode',
            'location',
            'public_phone',
            'contact_phone',
            'public_email',
            'website',
            'facebook_url',
            'x_twitter_url',
            'instagram_url',
            'categories',
            'accessibility_features',
            'description',
            'services_offered',
            'special_offers',
            'opening_hours',
            'logo',
            'membership_tier',
        ]
        labels = {
            'street_address1': 'Street address (building and number)',
            'street_address2': 'Address line 2 (suite, unit, etc.)',
        }

    def __init__(self, *args, **kwargs):
        """
        Initialises the form, sets queryset and default for membership tier,
        configures category and accessibility feature querysets, and ensures location is required.
        """
        super().__init__(*args, **kwargs)

        # Make address fields required
        self.fields['street_address1'].required = True
        self.fields['town_or_city'].required = True
        self.fields['county'].required = True
        self.fields['postcode'].required = True

        # only configure membership_tier if it still exists
        if 'membership_tier' in self.fields:
            self.fields['membership_tier'].queryset = MembershipTier.objects.filter(is_active=True)
            self.fields['membership_tier'].queryset = MembershipTier.objects.filter(is_active=True)
            self.fields['membership_tier'].empty_label = "Select a membership tier"
            try:
                free_tier = MembershipTier.objects.filter(tier__iexact='Free', is_active=True).first()
                if free_tier:
                    self.initial['membership_tier'] = free_tier.pk
            except MembershipTier.DoesNotExist:
                pass
        # Make location input required in HTML
        self.fields['location'].widget.attrs['required'] = True
        # purchase categories by group and name so grouping works correctly
        self.fields['categories'].queryset = Category.objects.all().order_by('group_description', 'name')
        self.fields['accessibility_features'].queryset = AccessibilityFeature.objects.all()

    def clean_location(self):
        """
        Ensure location WKT is parsed into a GEOS Point for the model field.
        Raises ValidationError if the input is missing or invalid.
        """
        from django.contrib.gis.geos import GEOSGeometry
        location = self.cleaned_data.get('location')
        if not location:
            raise forms.ValidationError('This field is required.')
        try:
            geom = GEOSGeometry(location)
        except Exception:
            raise forms.ValidationError('Invalid location format.')
        return geom

    def clean_logo(self):
        """
        Validates the uploaded logo file for allowed extensions and MIME types.
        Delegates further validation to a centralised validator.
        """
        logo = self.cleaned_data.get('logo')
        if not logo:
            return logo

        # Delegate to centralised validator (verify/reopen + size/dimension checks)
        validate_logo(logo, purpose="logo")
        return logo

    def clean_categories(self):
        """
        Ensures at least one category is provided.
        """
        categories = self.cleaned_data.get('categories')
        if not categories or not categories.exists():
            raise forms.ValidationError('Select at least one category.')
        return categories

    def save(self, commit=True):
        """
        Saves the business instance and its many-to-many relationships.
        """
        instance = super().save(commit=False)
        return instance


class BusinessUpdateForm(BusinessRegistrationForm):
    """
    Form for updating an existing business.

    - Inherits from BusinessRegistrationForm but removes the 'membership_tier' field.
    - Supports clearing (removing) the business logo.
    """
    class Meta(BusinessRegistrationForm.Meta):
        # remove the 'membership_tier' field from the registration form
        fields = [f for f in BusinessRegistrationForm.Meta.fields if f != 'membership_tier']

    def __init__(self, *args, **kwargs):
        """
        Initialises the form and removes the 'membership_tier' field.
        """
        super().__init__(*args, **kwargs)
        # pop it again in case parent __init__ already added it
        self.fields.pop('membership_tier', None)

    def clean_logo(self):
        """
        Handles clearing the logo if the clear checkbox is ticked.
        Returns None if the logo should be removed.
        """
        clear_name = f"{self.add_prefix('logo')}-clear"
        if self.data.get(clear_name):
            # wipe out the logo
            return None
        if 'logo' not in self.files or not self.files.get('logo'):
            return self.instance.logo
        return super().clean_logo()

    def save(self, commit=True):
        """
        Saves the updated business instance.
        Deletes the logo file from storage if the clear box was ticked.
        """
        instance = super().save(commit=False)
        # if the user ticked the clear box, kick off a delete
        clear_name = f"{self.add_prefix('logo')}-clear"
        if self.data.get(clear_name) and instance.logo:
            # deletes the file from storage
            instance.logo.delete(save=False)
            instance.logo = None
        if commit:
            instance.save()
            self.save_m2m()
        return instance
