from django.contrib import admin
from .models import Order

class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'stripe_checkout_session_id', 'stripe_payment_intent_id', 'stripe_subscription_id')
    # Explicitly define fields order in admin form
    fields = (
        'order_number', 'user', 'order_type', 'tier', 'interval',
        'stripe_price_id', 'total_amount', 'status',
        'stripe_checkout_session_id', 'stripe_payment_intent_id',
        'stripe_subscription_id', 'metadata'
    )
    # Define list display options for the admin interface
    list_display = ('order_number', 'email', 'full_name', 'order_type', 'tier', 'interval', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'email', 'full_name')
    ordering = ('-created_at',)


admin.site.register(Order, OrderAdmin)