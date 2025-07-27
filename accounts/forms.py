from PIL import Image

from allauth.account.forms import SignupForm
from django import forms
from .models import UserProfile

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user


class UserProfileForm(forms.ModelForm):
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            try:
                img = Image.open(photo)
                if img.width != img.height:
                    raise forms.ValidationError('Profile photo must be square (width and height must match).')
            except Exception:
                raise forms.ValidationError('Invalid image file.')
        return photo
    class Meta:
        model = UserProfile
        fields = [
            'country', 'county', 'photo', 'is_wheeler', 'has_business',
            'mobility_device', 'age_group'
        ]
