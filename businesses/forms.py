from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import Business, MembershipTier, AccessibilityFeature, Category
from core.widgets import MapLibrePointWidget
from core.validators import validate_logo


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
        help_text="Select the categories that describe your business. If yours isn't listed, choose 'Other' and enter it below.",
        required=False
    )
    other_category = forms.CharField(
        required=False,
        label="Other Category*",
        help_text="If your category isn't listed, type it here and it will be added to our database.",
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
        label="Business Location*",
        help_text="Find your business location on the map, zoom in for accuracy, and then click directly on your building or area to place a marker.",
        required=True,
    )
    # Use FileField so we can validate extension/MIME first in clean_logo
    logo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
        error_messages={
            'invalid': 'Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.'
        }
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
            'other_category',
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
        super().__init__(*args, **kwargs)
        
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
        logo = self.cleaned_data.get('logo')
        if not logo:
            return logo

        # Early extension/content-type check to give a clear "wrong file type" error for SVG
        name = getattr(logo, 'name', '') or ''
        content_type = getattr(logo, 'content_type', '') or ''
        allowed_exts = ('.png', '.jpg', '.jpeg', '.webp')
        allowed_mimes = ('image/png', 'image/jpeg', 'image/webp')

        if name and not name.lower().endswith(allowed_exts):
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")
        if content_type and content_type not in allowed_mimes:
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")

        # Delegate to centralized validator (verify/reopen + size/dimension checks)
        validate_logo(logo, purpose="logo")
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


class BusinessUpdateForm(BusinessRegistrationForm):
    class Meta(BusinessRegistrationForm.Meta):
        # remove the 'membership_tier' field from the registration form
        fields = [f for f in BusinessRegistrationForm.Meta.fields if f != 'membership_tier']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pop it again in case parent __init__ already added it
        self.fields.pop('membership_tier', None)
    
    def clean_logo(self):
        # if no new upload, leave the existing logo untouched
        if 'logo' not in self.files or not self.files.get('logo'):
            return self.instance.logo
        # otherwise do the usual validation
        return super().clean_logo()