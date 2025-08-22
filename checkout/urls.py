from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:business_id>/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
]