from django.contrib import admin
from .models import Purchase


class PurchaseAdmin(admin.ModelAdmin):
    # Make audit fields readonly
    readonly_fields = ('purchase_number', 'created_at', 'updated_at', 'stripe_payment_intent_id', 'raw_payload', 'metadata')

    # Use fieldsets for a compact, organized admin form. Address fields are
    # placed in a collapsible section; metadata/raw_payload are in an Audit
    # section at the bottom.
    fieldsets = (
        (None, {
            'fields': (
                'purchase_number',
                'purchase_type',
                'membership_tier',
                'business',
                'user',
                ('full_name', 'email'),
                'phone_number',
            )
        }),
        ('Address', {
            'classes': ('collapse',),
            'fields': (
                'street_address1',
                'street_address2',
                ('town_or_city', 'county', 'postcode'),
            )
        }),
        ('Payment & Status', {
            'fields': (
                'amount',
                'status',
                'stripe_payment_intent_id',
            )
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': (
                'metadata',
                'raw_payload',
                'created_at',
                'updated_at',
            )
        }),
    )
    # Define list display options for the admin interface
    list_display = ('purchase_number', 'purchase_type', 'membership_tier', 'business', 'user', 'email', 'amount', 'status', 'created_at')
    list_filter = ('purchase_type', 'status', 'created_at')
    search_fields = ('purchase_number', 'email', 'full_name', 'stripe_payment_intent_id')
    ordering = ('-created_at',)


admin.site.register(Purchase, PurchaseAdmin)
