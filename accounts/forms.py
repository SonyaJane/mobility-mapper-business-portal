from PIL import Image

from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model
from django import forms
from .models import UserProfile

class CustomSignupForm(SignupForm):
    confirm_email = forms.EmailField(max_length=254, required=True, label='Confirm Email Address')
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    # specify render order
    field_order = ['first_name', 'last_name', 'email', 'confirm_email', 'username', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data.get('email')  # ensure email from initial field
        user.save()
        return user
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm = cleaned_data.get('confirm_email')
        if email and confirm and email != confirm:
            self.add_error('confirm_email', 'Email addresses must match.')
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            # Validate that file is a valid image
            try:
                img = Image.open(photo)
            except Exception:
                raise forms.ValidationError('Invalid image file.')
            # Ensure the image is square
            if img.width != img.height:
                raise forms.ValidationError('Profile photo must be square (width and height must match).')
        return photo
    class Meta:
        model = UserProfile
        # Exclude system-managed flags; users cannot edit is_wheeler or has_business
        fields = [
            'country', 'county', 'photo', 'mobility_device', 'age_group'
        ]
