from django.contrib import admin
from .models import Purchase

class PurchaseAdmin(admin.ModelAdmin):
    readonly_fields = ('purchase_number', 'created_at', 'updated_at', 'stripe_payment_intent_id')
    # Explicitly define fields purchase in admin form
    fields = (
        'purchase_number', 'user', 'purchase_type', 'membership_tier', 'interval',
    'membership_stripe_price_id', 'amount', 'status',
    'stripe_payment_intent_id',
        'metadata'
    )
    # Define list display options for the admin interface
    list_display = ('purchase_number', 'email', 'full_name', 'purchase_type', 'membership_tier', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('purchase_number', 'email', 'full_name')
    ordering = ('-created_at',)


admin.site.register(Purchase, PurchaseAdmin)