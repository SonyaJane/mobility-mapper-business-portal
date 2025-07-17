from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.business_register, name='business_register'),
]
