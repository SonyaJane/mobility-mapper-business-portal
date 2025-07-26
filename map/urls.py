from django.urls import path
from . import views

urlpatterns = [
    path('route-finder/', views.route_finder, name='route_finder'),
    path('ajax/search-businesses/', views.ajax_search_businesses, name='ajax_search_businesses'),
]
