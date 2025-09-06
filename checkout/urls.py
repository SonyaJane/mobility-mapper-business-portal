from django.urls import path
from . import views
from .webhooks import webhook
urlpatterns = [
    # Checkout
    path('checkout/<int:business_id>/', views.checkout, name='checkout'),
    # Payment result pages
    path('payment-success/<str:purchase_number>/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('cache-checkout-data/', views.cache_checkout_data, name='cache_checkout_data'),
    path('webhook/', webhook, name='webhook'),
]