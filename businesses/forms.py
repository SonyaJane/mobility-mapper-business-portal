from django import forms
from .models import Business, WheelerVerification, ACCESSIBILITY_FEATURE_CHOICES
from .widgets import MapLibrePointWidget

class BusinessRegistrationForm(forms.ModelForm):
    accessibility_features = forms.MultipleChoiceField(
        choices=ACCESSIBILITY_FEATURE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Business
        exclude = [
            'owner',
            'wheeler_verification_requested',
            'verified_by_wheelers',
            'wheeler_verification_notes',
            'is_approved',
        ]
        widgets = {
            'location': MapLibrePointWidget(),
        }
        
    def clean_accessibility_features(self):
        # Store the list as JSON
        data = self.cleaned_data['accessibility_features']
        return list(data)


class WheelerVerificationForm(forms.ModelForm):
    class Meta:
        model = WheelerVerification
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }
        
