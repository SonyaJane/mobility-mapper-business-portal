from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_business, name='register_business'),
    path('dashboard/', views.business_dashboard, name='business_dashboard'),
    path('edit/', views.edit_business, name='edit_business'),
    path('delete/', views.delete_business, name='delete_business'),
    path('<int:pk>/wheeler-verification-application/', views.wheeler_verification_application, name='wheeler_verification_application'),
    path('<int:pk>/request-wheelers-verification/', views.business_request_wheeler_verification, name='business_request_wheeler_verification'),
    path('<int:pk>/verify/', views.wheeler_verification_form, name='wheeler_verification_form'),
    path('pending-verifications/', views.pending_verification_requests, name='pending_verification_requests'),
    path('verification-report/<int:verification_id>/', views.verification_report, name='verification_report'),
    path('wheeler-verification-history/', views.wheeler_verification_history, name='wheeler_verification_history'),
    path('<int:business_id>/cancel-verification-request/', views.cancel_wheeler_verification_request, name='cancel_wheeler_verification_request'),
    # Membership cancellation endpoint
    path('cancel-membership/', views.cancel_membership, name='cancel_membership'),
    path('accessible-business-search/', views.accessible_business_search, name='accessible_business_search'),
    path('ajax/search-businesses/', views.ajax_search_businesses, name='ajax_search_businesses'),
    # Public-facing business detail page
    path('<int:pk>/', views.business_detail, name='business_detail'),
    path('plans/', views.explore_plans, name='explore_plans'),
]
