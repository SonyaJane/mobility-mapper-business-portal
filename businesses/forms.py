from django import forms
from .models import Business, ACCESSIBILITY_FEATURE_CHOICES
from .widgets import MapLibrePointWidget

class BusinessRegistrationForm(forms.ModelForm):
    accessibility_features = forms.MultipleChoiceField(
        choices=ACCESSIBILITY_FEATURE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Business
        exclude = ('owner', 'is_approved',)
        widgets = {
            'location': MapLibrePointWidget(),
        }
        
    def clean_accessibility_features(self):
        # Store the list as JSON
        data = self.cleaned_data['accessibility_features']
        return list(data)
