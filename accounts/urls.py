from django.urls import path
from . import views

urlpatterns = [
    path('account_dashboard/', views.dashboard_view, name='account_dashboard'),
]
