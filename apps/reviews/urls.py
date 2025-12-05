"""
URL configuration for reviews app.
"""

from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Review assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/<uuid:pk>/', views.review_interface, name='review_interface'),
    path('assignments/<uuid:pk>/save_score/', views.save_review_score, name='save_review_score'),
    path('assignments/<uuid:pk>/submit/', views.review_submit, name='review_submit'),
    
    # COI declaration
    path('coi/declare/<uuid:application_id>/', views.declare_coi, name='declare_coi'),
]
