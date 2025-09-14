from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_business, name='register_business'),
    path('dashboard/', views.business_dashboard, name='business_dashboard'),
    path('edit/', views.edit_business, name='edit_business'),
    path('delete/', views.delete_business, name='delete_business'),
    path('cancel-membership/', views.cancel_membership, name='cancel_membership'),
    path('accessible-business-search/', views.accessible_business_search, name='accessible_business_search'),
    path('ajax/search-businesses/', views.ajax_search_businesses, name='ajax_search_businesses'),
    path('upgrade-membership/', views.upgrade_membership, name='upgrade_membership'),
    path('current-membership/', views.view_existing_membership, name='view_existing_membership'),
]
