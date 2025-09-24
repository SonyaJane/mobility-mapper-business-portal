from django.urls import path
from . import views

urlpatterns = [    
    path('<int:pk>/wheeler-verification-application/', views.wheeler_verification_application, name='wheeler_verification_application'),
    path('application-submitted/<int:pk>/', views.application_submitted, name='application_submitted'),
    path('<int:pk>/request-wheeler-verification/', views.request_wheeler_verification, name='request_wheeler_verification'),
    path('<int:pk>/verify/', views.wheeler_verification_form, name='wheeler_verification_form'),
    path('verification-report/<int:verification_id>/', views.verification_report, name='verification_report'),
    path('accessibility-verification-hub/', views.accessibility_verification_hub, name='accessibility_verification_hub'),
    path('<int:business_id>/cancel-verification-application/', views.cancel_wheeler_verification_application, name='cancel_wheeler_verification_application'),
    path('<int:pk>/', views.business_detail, name='business_detail'),
]
