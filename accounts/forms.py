from PIL import Image

from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model
from django import forms
from .models import UserProfile

class CustomSignupForm(SignupForm):
    confirm_email = forms.EmailField(max_length=254, required=True, label='Confirm Email Address')
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    # Override username for custom label
    username = forms.CharField(max_length=150, required=True, label='Choose a username')
    # New profile questions
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
    mobility_devices = forms.MultipleChoiceField(
        choices=UserProfile.MOBILITY_DEVICE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Which mobility devices do you use?'
    )
    mobility_devices_other = forms.CharField(
        max_length=100,
        required=False,
        label='Please specify other mobility device',
        widget=forms.TextInput(attrs={'placeholder': 'Describe other device'})
    )
    # Additional profile fields
    country = forms.ChoiceField(
        choices=UserProfile.COUNTRY_CHOICES,
        initial='UK',
        label='Country',
        required=True
    )
    county = forms.ChoiceField(
        choices=UserProfile.UK_COUNTY_CHOICES,
        label='County',
        required=False
    )
    age_group = forms.ChoiceField(
        choices=UserProfile.AGE_GROUP_CHOICES,
        label='Age Group',
        required=False
    )
    photo = forms.ImageField(
        label='Profile Photo',
        required=False
    )
    # specify render order including new fields
    field_order = [
        'first_name', 'last_name', 
        'email', 'confirm_email', 'username', 
        'has_business', 'is_wheeler', 'mobility_devices', 'mobility_devices_other', 
        'country', 'county', 'age_group', 'photo',
        'password1', 'password2'
    ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm = cleaned_data.get('confirm_email')
        if email and confirm and email != confirm:
            self.add_error('confirm_email', 'Email addresses must match.')
        # Require other device description if 'Other' selected
        devices = cleaned_data.get('mobility_devices', []) or []
        other_desc = cleaned_data.get('mobility_devices_other', '').strip()
        if 'other' in devices and not other_desc:
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
        profile = user.userprofile
        profile.has_business = self.cleaned_data.get('has_business', False)
        profile.is_wheeler = self.cleaned_data.get('is_wheeler', False)
        # Only set devices if wheeler
        if profile.is_wheeler:
            profile.mobility_devices = self.cleaned_data.get('mobility_devices', [])
            profile.mobility_devices_other = self.cleaned_data.get('mobility_devices_other', '')
        else:
            profile.mobility_devices = []
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
    # Render mobility_devices as checkboxes, and allow free-text for 'other'
    mobility_devices = forms.MultipleChoiceField(
        choices=UserProfile.MOBILITY_DEVICE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Which mobility devices do you use?'
    )
    mobility_devices_other = forms.CharField(
        max_length=100,
        required=False,
        label='Please specify other device'
    )
    # Business ownership and wheeler flags
    has_business = forms.TypedChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Do you own or manage a business?'
    )
    is_wheeler = forms.TypedChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Do you use a wheeled mobility device?'
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate initial values for overridden fields
        if hasattr(self, 'instance') and self.instance:
            # User name
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            # Mobility devices
            self.fields['mobility_devices'].initial = self.instance.mobility_devices or []
            self.fields['mobility_devices_other'].initial = self.instance.mobility_devices_other or ''
            # Business and wheeler flags
            self.fields['has_business'].initial = self.instance.has_business
            self.fields['is_wheeler'].initial = self.instance.is_wheeler

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            try:
                img = Image.open(photo)
            except Exception:
                raise forms.ValidationError('Invalid image file.')
            if img.width != img.height:
                raise forms.ValidationError('Profile photo must be square (width and height must match).')
            # Reset file pointer after PIL read so storage uploads full content
            photo.file.seek(0)
        return photo

    class Meta:
        model = UserProfile
        # mobility_devices and mobility_devices_other handled in save()
        fields = ['country', 'county', 'photo', 'age_group']

    def save(self, commit=True):
        # Save profile fields and customized mobility selections
        profile = super().save(commit=False)
        # Save business and mobility flags
        profile.has_business = self.cleaned_data.get('has_business', False)
        profile.is_wheeler = self.cleaned_data.get('is_wheeler', False)
        # Update mobility devices list
        if profile.is_wheeler:
            profile.mobility_devices = self.cleaned_data.get('mobility_devices', [])
        else:
            profile.mobility_devices = []
        # Update other device text or clear if unchecked
        profile.mobility_devices_other = self.cleaned_data.get('mobility_devices_other', '')
        # Save related user name
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        if commit:
            user.save()
            profile.save()
        return profile
