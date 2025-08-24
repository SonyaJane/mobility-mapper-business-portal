from django.urls import path
from . import views

urlpatterns = [
    # Subscription checkout
    path('checkout/subscription/<int:business_id>/', views.checkout_subscription, name='checkout_subscription'),
    # One-off Wheeler verification checkout
    path('checkout/wheeler/<int:business_id>/', views.checkout_wheeler_verification, name='checkout_wheeler_verification'),
    # Payment result pages
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
]