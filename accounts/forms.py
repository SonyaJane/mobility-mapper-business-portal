from django import forms
from core.validators import validate_profile_photo
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model

from .models import UserProfile, County, AgeGroup, MobilityDevice

User = get_user_model()

class CustomSignupForm(SignupForm):
    """
    Extended signup form integrating additional profile fields:
    - Name, username, and email confirmation
    - Business ownership and wheeler status
    - Mobility devices (multi-select + 'other' text)
    - Location (country, county) and age group
    - Optional profile photo with validation
    Handles conditional requirements (e.g., mobility devices when 'is_wheeler' is true)
    and synchronizes data into the related UserProfile on save.
    """
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
        required=True,
        empty_label='Select county'
    )
    age_group = forms.ModelChoiceField(
        queryset=AgeGroup.objects.all(),
        label='Age Group',
        required=True,
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
        """
        Validate the username:
        - Required
        - Case-insensitive uniqueness check against existing users.
        Returns the cleaned username or raises ValidationError.
        """
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Username is required.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_photo(self):
        """
        Validate the uploaded profile photo:
        - Ensures allowed extensions (png, jpg, jpeg, webp)
        - Ensures allowed MIME types
        - Delegates full validation (size, dimensions, integrity) to validate_profile_photo.
        Returns the validated file or None if not provided.
        """
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        name = getattr(photo, 'name', '') or ''
        content_type = getattr(photo, 'content_type', '') or ''
        allowed_exts = ('.png', '.jpg', '.jpeg', '.webp')
        allowed_mimes = ('image/png', 'image/jpeg', 'image/webp')

        if name and not name.lower().endswith(allowed_exts):
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")
        if content_type and content_type not in allowed_mimes:
            raise ValidationError("Please upload a PNG, JPEG or WEBP image. SVG or other formats are not allowed.")

        return validate_profile_photo(photo, purpose="profile photo")

    def clean(self):
        """
        Perform cross-field validation:
        - If is_wheeler is true, at least one mobility device is required.
        - If 'Other' mobility device selected, require description.
        - Confirm email and confirm_email must match (case-insensitive).
        Adds field-specific errors where appropriate and returns cleaned_data.
        """
        cleaned_data = super().clean()
        is_wheeler = cleaned_data.get('is_wheeler')
        mobility_devices = cleaned_data.get('mobility_devices')
        if is_wheeler and (not mobility_devices or len(mobility_devices) == 0):
            self.add_error('mobility_devices', 'Please select at least one mobility device.')
        other_desc = (cleaned_data.get('mobility_devices_other') or '').strip()
        if mobility_devices and any(getattr(d, 'code', '').lower() == 'other' for d in mobility_devices) and not other_desc:
            self.add_error('mobility_devices_other', 'Please specify your other mobility device.')
        email = cleaned_data.get('email')
        confirm = cleaned_data.get('confirm_email')
        if email and confirm and email.lower() != confirm.lower():
            self.add_error('confirm_email', 'Email addresses must match.')
        return cleaned_data

    def save(self, request):
        """
        Persist the User and associated UserProfile:
        - Updates core User fields (first_name, last_name, email).
        - Creates or updates the related UserProfile.
        - Conditionally assigns mobility devices and 'other' text only if is_wheeler is true.
        - Saves optional photo if provided.
        Returns the saved User instance.
        """
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data.get('email')
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.has_business = self.cleaned_data.get('has_business', False)
        profile.is_wheeler = self.cleaned_data.get('is_wheeler', False)
        if profile.is_wheeler:
            profile.mobility_devices.set(self.cleaned_data.get('mobility_devices', []))
            profile.mobility_devices_other = self.cleaned_data.get('mobility_devices_other', '')
        else:
            profile.mobility_devices.clear()
            profile.mobility_devices_other = ''
        profile.country = self.cleaned_data.get('country')
        profile.county = self.cleaned_data.get('county')
        profile.age_group = self.cleaned_data.get('age_group')
        photo = self.cleaned_data.get('photo')
        if photo:
            profile.photo = photo
        profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for editing existing user profile data:
    - Allows updating personal names, business/wheeler flags
    - Manages mobility devices (multi-select + other), age group, location, and photo
    - Applies conditional clearing of mobility-related fields when user is not a wheeler
    Ensures synchronization between User and UserProfile models.
    """
    first_name = forms.CharField(
        max_length=30, 
        required=True, label='First Name')
    last_name = forms.CharField(
        max_length=30, 
        required=True, label='Last Name')
    age_group = forms.ModelChoiceField(
        queryset=AgeGroup.objects.all(),
        required=True,
        empty_label=None
    )
    country = forms.ChoiceField(
        choices=UserProfile.COUNTRY_CHOICES,
        initial='UK',
        label='Country',
        required=True
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
        """
        Configuration for the model form specifying model binding and editable fields.
        """
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'has_business', 'is_wheeler',
            'mobility_devices', 'mobility_devices_other',
            'country', 'county', 'age_group', 'photo'
        ]
        
    def __init__(self, *args, **kwargs):
        """
        Initialize the form:
        - Prefills first/last name from related User.
        - Sets initial values for profile-related fields when editing an existing instance.
        Ensures consistency with TypedChoiceField expectations (string values).
        """
        super().__init__(*args, **kwargs)
        user = getattr(self.instance, 'user', None)
        if user is not None:
            self.fields['first_name'].initial = getattr(user, 'first_name', '')
            self.fields['last_name'].initial = getattr(user, 'last_name', '')
        if getattr(self.instance, 'pk', None) and user is not None:
            self.fields['country'].initial = self.instance.country
            self.fields['mobility_devices'].initial = list(self.instance.mobility_devices.values_list('pk', flat=True))
            self.fields['mobility_devices_other'].initial = self.instance.mobility_devices_other or ''
            self.fields['has_business'].initial = 'True' if self.instance.has_business else 'False'
            self.fields['is_wheeler'].initial = 'True' if self.instance.is_wheeler else 'False'

    def clean_photo(self):
        """
        Validate the uploaded photo (if any):
        - Rejects disallowed extensions/MIME types early (e.g. SVG)
        - Delegates deep validation to validate_profile_photo
        Returns validated file or None.
        """
        # Check if 'delete current photo' was ticked
        clear_name = f"{self.add_prefix('photo')}-clear"
        if self.data.get(clear_name):
            # signal deletion
            return False

        # No new upload, keep existing photo, skip all validation
        if 'photo' not in self.files or not self.files.get('photo'):
            return getattr(self.instance, 'photo', None)

        # New upload do validation
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        return validate_profile_photo(photo, purpose="profile photo")

    def clean(self):
        """
        Perform cross-field validation for mobility devices:
        - If 'Other' device is selected, require a description in 'mobility_devices_other'.
        - Only applies validation if at least one device is selected.
        - Adds an error to 'mobility_devices_other' if required and missing.
        - Returns cleaned data after adding any field errors.
        """
        cleaned = super().clean()
        devices = cleaned.get('mobility_devices') or []
        other_desc = (cleaned.get('mobility_devices_other') or '').strip()
        if any(getattr(d, 'code', '').lower() == 'other' for d in devices) and not other_desc:
            self.add_error('mobility_devices_other', 'Please specify your other mobility device.')
        return cleaned

    def save(self, commit=True):
        """
        Save changes to the user profile and synchronize related User fields:
        - Updates business ownership and wheeler status flags.
        - Clears mobility devices and 'other' text if the user is no longer a wheeler.
        - Handles optional profile photo removal if requested.
        - Saves many-to-many mobility device relations only if the user is a wheeler.
        Returns the updated UserProfile instance.
        """
        # handle photo deletion if requested
        original_photo = getattr(self.instance, 'photo', None)
        profile = super().save(commit=False) # get unsaved profile instance
        # if "clear" was ticked, delete the original file from storage
        if self.cleaned_data.get('photo') is False and original_photo:
            original_photo.delete(save=False)
            profile.photo = None

        # update profile fields from form data
        profile.has_business = self.cleaned_data.get('has_business', False)
        profile.is_wheeler = self.cleaned_data.get('is_wheeler', False)
        profile.country = self.cleaned_data.get('country') or ''
        profile.county = self.cleaned_data.get('county') or None
        profile.age_group = self.cleaned_data.get('age_group') or None
        # only set mobility devices if user is a wheeler
        if profile.is_wheeler:
            profile.mobility_devices_other = self.cleaned_data.get('mobility_devices_other', '')
        else:
            profile.mobility_devices_other = ''
        user = profile.user
        # update user fields from form data
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        
        # save both user and profile if commit=True
        if commit:
            user.save()
            profile.save()
            if profile.is_wheeler:
                self.save_m2m()
            else:
                profile.mobility_devices.clear()
        return profile
