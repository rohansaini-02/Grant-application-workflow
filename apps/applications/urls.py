"""
URL configuration for applications app.
"""

from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Application list and detail
    path('', views.application_list, name='list'),
    path('<uuid:pk>/', views.application_detail, name='detail'),
    path('create/', views.application_create, name='create'),
    path('<uuid:pk>/edit/', views.application_edit, name='edit'),
    path('<uuid:pk>/submit/', views.application_submit, name='submit'),
    
    # Version history
    path('<uuid:pk>/versions/', views.version_history, name='version_history'),
    
    # Document management
    path('<uuid:pk>/documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:doc_id>/delete/', views.document_delete, name='document_delete'),
]
