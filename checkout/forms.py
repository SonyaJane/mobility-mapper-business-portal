from django import forms
from .models import Purchase

class PurchaseForm(forms.ModelForm):
    """Form for creating a Purchase for on-site Stripe Elements (PaymentIntent) payments."""

    class Meta:
        model = Purchase
        fields = [
            'full_name', 'email', 'phone_number',
            'street_address1', 'street_address2',
            'town_or_city', 'county', 'postcode',
            'membership_tier',
        ]
        labels = {
            'full_name': 'Full Name',
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'street_address1': 'Address Line 1',
            'street_address2': 'Address Line 2',
            'town_or_city': 'Town or City',
            'county': 'County',
            'postcode': 'Postal Code',
            'membership_tier': 'Tier',
        }
        widgets = {
            'purchase_type': forms.HiddenInput(),
            'membership_tier': forms.HiddenInput(),
        }
        
    def __init__(self, *args, **kwargs):
        """
        Add placeholders and classes, remove auto-generated
        labels and set autofocus on first field
        """
        super().__init__(*args, **kwargs)
        placeholders = {
            'full_name': 'Full Name',
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'street_address1': 'Street Address 1',
            'street_address2': 'Street Address 2',
            'town_or_city': 'Town or City',
            'county': 'County',
            'postcode': 'Postal Code',            
        }
        self.fields['full_name'].widget.attrs['autofocus'] = True
        for field in self.fields:
            # Only set placeholders for fields in our placeholder map
            if field in placeholders:
                if self.fields[field].required:
                    placeholder = f'{placeholders[field]} *'
                else:
                    placeholder = placeholders[field]
                self.fields[field].widget.attrs['placeholder'] = placeholder
            # Add styling class and hide labels for all fields
            self.fields[field].widget.attrs['class'] = 'stripe-style-input'

