from leaflet.forms.widgets import LeafletWidget
from django import forms
from .models import Business

class BusinessRegistrationForm(forms.ModelForm):
    class Meta:
        model = Business
        exclude = ('owner', 'is_verified',)
        widgets = {
            'location': LeafletWidget(),
        }
