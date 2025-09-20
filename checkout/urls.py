from . import views
from django.urls import path
from .webhooks import webhook

urlpatterns = [
    path('checkout/<int:business_id>/', views.checkout, name='checkout'),
    path('payment-success/<str:purchase_number>/', views.payment_success, name='payment_success'),
    path('cache-checkout-data/', views.cache_checkout_data, name='cache_checkout_data'),
    path('webhook/', webhook, name='webhook'),
]
