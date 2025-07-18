from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('test-toasts/', views.test_toasts, name='test_toasts'),
]