from core.validators import validate_profile_photo
from django import forms
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model

from .models import UserProfile, County, AgeGroup, MobilityDevice

User = get_user_model()

class CustomSignupForm(SignupForm):
    confirm_email = forms.EmailField(max_length=254, required=True, label='Confirm Email Address')
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    username = forms.CharField(max_length=150, required=True, label='Choose a username')

    has_business = forms.TypedChoiceField(
        choices=[('True', 'Yes'), ('False', 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Do you own or manage a business?'
    )
    is_wheeler = forms.TypedChoiceField(
        choices=[('True', 'Yes'), ('False', 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Do you use a wheeled mobility device?'
    )
    mobility_devices = forms.ModelMultipleChoiceField(
        queryset=MobilityDevice.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Which mobility devices do you use?'
    )
    mobility_devices_other = forms.CharField(
        max_length=100,
        required=False,
        label='Please specify other mobility device',
        widget=forms.TextInput(attrs={'placeholder': 'Specify other device'})
    )
    country = forms.ChoiceField(
        choices=UserProfile.COUNTRY_CHOICES,
        initial='UK',
        label='Country',
        required=True
    )
    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        label='County',
        required=False,
        empty_label='Select county'
    )
    age_group = forms.ModelChoiceField(
        queryset=AgeGroup.objects.all(),
        label='Age Group',
        required=False,
        empty_label='Select age group'
    )
    photo = forms.FileField(
        label='Profile Photo',
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
        error_messages={
            'invalid': 'Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.'
        }
    )
    field_order = [
        'first_name', 'last_name', 
        'email', 'confirm_email', 'username', 
        'has_business', 'is_wheeler', 'mobility_devices', 'mobility_devices_other', 
        'country', 'county', 'age_group', 'photo',
        'password1', 'password2'
    ]

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Username is required.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        # Early extension / MIME hint check -> "wrong file type" message for SVG etc.
        name = getattr(photo, 'name', '') or ''
        content_type = getattr(photo, 'content_type', '') or ''
        allowed_exts = ('.png', '.jpg', '.jpeg', '.webp')
        allowed_mimes = ('image/png', 'image/jpeg', 'image/webp')

        # Early "wrong file type" check (catches SVG, etc.)
        if name and not name.lower().endswith(allowed_exts):
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")
        if content_type and content_type not in allowed_mimes:
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")

        # Delegate to centralized validator (verify/reopen + size/dimension checks)
        return validate_profile_photo(photo, purpose="profile photo")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm = cleaned_data.get('confirm_email')
        if email and confirm and email.lower() != confirm.lower():
            self.add_error('confirm_email', 'Email addresses must match.')
            
        # Require other device description if 'Other' selected
        devices = cleaned_data.get('mobility_devices', []) or []
        other_desc = cleaned_data.get('mobility_devices_other', '').strip()
        # devices is a queryset/list of MobilityDevice instances; check their code
        if any(getattr(d, 'code', '').lower() == 'other' for d in devices) and not other_desc:
            self.add_error('mobility_devices_other', 'Please specify your other mobility device.')
        # No immediate validation for country/county/age/photo
        return cleaned_data

    def save(self, request):
        user = super().save(request)
        # Save name and email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data.get('email')
        user.save()
        # Save profile flags
        # Ensure profile exists and use related_name 'profile'
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.has_business = self.cleaned_data.get('has_business', False)
        profile.is_wheeler = self.cleaned_data.get('is_wheeler', False)
        # Only set devices if wheeler
        if profile.is_wheeler:
            profile.mobility_devices.set(self.cleaned_data.get('mobility_devices', []))
            profile.mobility_devices_other = self.cleaned_data.get('mobility_devices_other', '')
        else:
            profile.mobility_devices.clear()
            profile.mobility_devices_other = ''
        # Save additional profile fields
        profile.country = self.cleaned_data.get('country')
        profile.county = self.cleaned_data.get('county')
        profile.age_group = self.cleaned_data.get('age_group')
        photo = self.cleaned_data.get('photo')
        if photo:
            profile.photo = photo
        profile.save()
        return user

# Model form for editing user profile
class UserProfileForm(forms.ModelForm):
    # Include user name fields
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    # Country field (extend model)
    country = forms.ChoiceField(
        choices=UserProfile.COUNTRY_CHOICES,
        initial='UK',
        label='Country',
        required=True
    )
    # Render mobility_devices as checkboxes, and allow free-text for 'other'
    mobility_devices = forms.ModelMultipleChoiceField(
        queryset=MobilityDevice.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Which mobility devices do you use?'
    )
    mobility_devices_other = forms.CharField(
        max_length=100,
        required=False,
        label='Please specify other device',
        widget=forms.TextInput(attrs={'placeholder': 'Specify other device'})
    )
    
    photo = forms.FileField(
        label='Profile Photo',
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
        error_messages={
            'invalid': 'Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.'
        }
    )

    # Business ownership and wheeler flags
    has_business = forms.TypedChoiceField(
        choices=[('True', 'Yes'), ('False', 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Do you own or manage a business?'
    )
    is_wheeler = forms.TypedChoiceField(
        choices=[('True', 'Yes'), ('False', 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Do you use a wheeled mobility device?'
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'has_business', 'is_wheeler',
            'mobility_devices', 'mobility_devices_other',
            'country', 'county', 'age_group', 'photo'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate initial values for overridden fields
        if hasattr(self, 'instance') and self.instance:
            # User name
            self.fields['first_name'].initial = getattr(self.instance.user, 'first_name', '')
            self.fields['last_name'].initial = getattr(self.instance.user, 'last_name', '')
            # Country
            self.fields['country'].initial = self.instance.country
            # Mobility devices: use list of PKs
            self.fields['mobility_devices'].initial = list(self.instance.mobility_devices.values_list('pk', flat=True))
            self.fields['mobility_devices_other'].initial = self.instance.mobility_devices_other or ''
            # Business and wheeler flags (use string values to match TypedChoiceField choices)
            self.fields['has_business'].initial = 'True' if self.instance.has_business else 'False'
            self.fields['is_wheeler'].initial = 'True' if self.instance.is_wheeler else 'False'

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        # Early extension / MIME hint check -> "wrong file type" message for SVG etc.
        name = getattr(photo, 'name', '') or ''
        content_type = getattr(photo, 'content_type', '') or ''
        allowed_exts = ('.png', '.jpg', '.jpeg', '.webp')
        allowed_mimes = ('image/png', 'image/jpeg', 'image/webp')

        if name and not name.lower().endswith(allowed_exts):
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")
        if content_type and content_type not in allowed_mimes:
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")

        # Delegate to centralized validator (verify/reopen + size/dimension checks)
        return validate_profile_photo(photo, purpose="profile photo")

    def clean(self):
        cleaned = super().clean()
        devices = cleaned.get('mobility_devices') or []
        other_desc = (cleaned.get('mobility_devices_other') or '').strip()
        if any(getattr(d, 'code', '').lower() == 'other' for d in devices) and not other_desc:
            self.add_error('mobility_devices_other', 'Please specify your other mobility device.')
        return cleaned

    def save(self, commit=True):
        # Save profile fields and customized mobility selections
        profile = super().save(commit=False)
        # Save business and mobility flags
        profile.has_business = self.cleaned_data.get('has_business', False)
        profile.is_wheeler = self.cleaned_data.get('is_wheeler', False)
        # Update other device text only when wheeler; clear otherwise
        if profile.is_wheeler:
            profile.mobility_devices_other = self.cleaned_data.get('mobility_devices_other', '')
        else:
            profile.mobility_devices_other = ''
        # Save related user name
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        if commit:
            user.save()
            profile.save()
            # Persist many-to-many only when wheeler; clear otherwise
            if profile.is_wheeler:
                # let the ModelForm handle m2m from cleaned_data
                self.save_m2m()
            else:
                profile.mobility_devices.clear()
        return profile
