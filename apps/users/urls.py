"""
URL configuration for users app.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Dashboard routing
    path('', views.dashboard, name='dashboard'),
    path('applicant/', views.applicant_dashboard, name='applicant_dashboard'),
    path('reviewer/', views.reviewer_dashboard, name='reviewer_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Admin User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/dashboard/login/'), name='logout'),
]
