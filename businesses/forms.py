from django import forms
from .models import Business

class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = Business
        exclude = ('owner', 'is_verified',)
