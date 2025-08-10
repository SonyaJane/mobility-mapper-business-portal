from django.urls import path
from . import views

urlpatterns = [
    path('account_dashboard/', views.dashboard_view, name='account_dashboard'),
    path('postlogin/', views.postlogin_redirect, name='postlogin_redirect'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('validate-username/', views.validate_username, name='validate_username'),
]
