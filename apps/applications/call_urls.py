"""
URL configuration for calls.
"""

from django.urls import path
from . import call_views

app_name = 'calls'

urlpatterns = [
    path('', call_views.call_list, name='list'),
    path('<uuid:pk>/', call_views.call_detail, name='detail'),
    path('create/', call_views.call_create, name='create'),
    path('<uuid:pk>/edit/', call_views.call_edit, name='edit'),
]
