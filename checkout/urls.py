from django.urls import path
from . import views
from .webhooks import webhook
urlpatterns = [
    # Checkout
    path('checkout/<int:business_id>/', views.checkout, name='checkout'),
    # Payment result pages
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('payment-status/', views.payment_status, name='payment_status'),
    path('webhook/', webhook, name='webhook'),
]