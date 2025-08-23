from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    """Form for creating an Order via Stripe Checkout."""

    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone_number',
            'street_address1', 'street_address2', 
            'town_or_city', 'county', 'postcode',
            'tier', 'interval'
        ]
        widgets = {
            'tier': forms.RadioSelect(),
            'interval': forms.RadioSelect(),
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
            self.fields[field].label = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('order_type') == 'subscription':
            if not cleaned_data.get('tier'):
                self.add_error('tier', 'Please select a subscription tier.')
            if not cleaned_data.get('interval'):
                self.add_error('interval', 'Please select a billing interval.')
        return cleaned_data