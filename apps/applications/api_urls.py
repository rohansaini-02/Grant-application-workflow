"""
API URL configuration for applications app.
"""

from django.urls import path
from . import api_views

app_name = 'applications_api'

urlpatterns = [
    path('applications/', api_views.ApplicationListView.as_view(), name='application_list'),
    path('applications/<uuid:pk>/', api_views.ApplicationDetailView.as_view(), name='application_detail'),
]
