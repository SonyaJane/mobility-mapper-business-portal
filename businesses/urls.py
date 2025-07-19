from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_business, name='register_business'),
    path('dashboard/', views.business_dashboard, name='business_dashboard'),
    path('edit/', views.edit_business, name='edit_business'),
    path('delete/', views.delete_business, name='delete_business'),
    path('<int:pk>/request-wheeler-verification/', views.request_wheeler_verification, name='request_wheeler_verification'),
    path('<int:pk>/verify/', views.submit_wheeler_verification, name='submit_verification'),
    path('public/<int:pk>/', views.public_business_detail, name='public_business_detail'),
    path('directory/', views.public_business_list, name='public_business_list'),
]
