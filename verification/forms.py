from django import forms
from .models import WheelerVerification
from .models import AccessibilityFeature


class WheelerVerificationForm(forms.ModelForm):
    # verify business accessibility features
    confirmed_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.CheckboxSelectMultiple,  # built-in checkbox widget
        required=False  # allows no selections
    )
    additional_features = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = WheelerVerification
        # Include selfie field for Wheeler’s photo
        fields = ['confirmed_features', 'additional_features', 'comments', 'selfie']
        field_classes = {'selfie': forms.ImageField}
        widgets = {
            'comments': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Please describe your accessibility experience.',
                'class': 'form-control w-100',
                'style': 'max-width: 100%;',
            }),
        }
    selfie = forms.ImageField(required=True, label="Upload a photo of yourself")

    def __init__(self, *args, **kwargs):
        business = kwargs.pop('business', None)  # optional business instance to filter features
        super().__init__(*args, **kwargs)

        # Ensure self.data is mutable so we can strip blank values
        if hasattr(self.data, 'copy'):
            data = self.data.copy()  # make mutable QueryDict copy
            if hasattr(data, 'getlist'):
                confirmed_vals = [v for v in data.getlist('confirmed_features') if v]
                data.setlist('confirmed_features', confirmed_vals)
            self.data = data

        # confirmed_features = those currently assigned to this business (guard business None)
        if business is not None:
            confirmed_qs = business.accessibility_features.all()
        else:
            confirmed_qs = AccessibilityFeature.objects.none()
        self.fields['confirmed_features'].queryset = confirmed_qs

        # Additional features = all features minus those already assigned to this business
        self.fields['additional_features'].queryset = AccessibilityFeature.objects.exclude(
            pk__in=confirmed_qs.values_list('pk', flat=True)
        )

    def clean(self):
        cleaned_data = super().clean()
        # Ensure a mobility device is selected
        if not (self.data.get('mobility_device')):
            raise forms.ValidationError('Select the mobility device you are using.')
        confirmed = cleaned_data.get('confirmed_features') or []
        additional = cleaned_data.get('additional_features') or []
        errors = []
        # Check that for each selected feature a photo was uploaded
        for feature in confirmed:
            if f'feature_photo_{feature.pk}' not in (self.files or {}):
                errors.append(forms.ValidationError(
                    f"A photo is required for confirmed feature '{feature.name}'."
                ))
        for feature in additional:
            if f'feature_photo_{feature.pk}' not in (self.files or {}):
                errors.append(forms.ValidationError(
                    f"A photo is required for additional feature '{feature.name}'."
                ))
        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data
