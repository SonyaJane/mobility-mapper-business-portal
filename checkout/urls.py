from django.urls import path
from . import views

urlpatterns = [
    # Checkout
    path('checkout/checkout/<int:business_id>/', views.checkout, name='checkout'),
    # Payment result pages
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
]