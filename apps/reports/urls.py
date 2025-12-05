"""
URL configuration for reports app.
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    
    # Exports
    path('export/applications/', views.export_applications, name='export_applications'),
    path('export/reviews/', views.export_reviews, name='export_reviews'),
    path('export/feedback/<uuid:application_id>/', views.export_feedback_packet, name='export_feedback'),
    
    # Downloads
    path('download/<uuid:access_token>/', views.download_export, name='download'),
]
