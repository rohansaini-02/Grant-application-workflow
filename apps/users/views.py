"""
Views for user management and dashboards.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import User
from .forms import UserRegistrationForm, ProfileEditForm
from .permissions import applicant_required, reviewer_required, admin_required


def register(request):
    """Register a new user with role selection."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # If registering as admin, grant full Django admin access
            if user.role == 'ADMIN':
                user.is_staff = True
                user.is_superuser = True
            user.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created as {user.get_role_display()}.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'users/register.html', {'form': form})


@login_required
def dashboard(request):
    """
    Route users to their role-specific dashboard.
    """
    user = request.user
    
    if user.is_admin_user():
        return redirect('admin_dashboard')
    elif user.is_reviewer():
        return redirect('reviewer_dashboard')
    elif user.is_applicant():
        return redirect('applicant_dashboard')
    else:
        messages.error(request, "Invalid user role.")
        return redirect('login')


@applicant_required
def applicant_dashboard(request):
    """Dashboard for applicants with comprehensive application status."""
    from apps.applications.models import Application
    
    applications = Application.objects.filter(applicant=request.user).order_by('-created_at')
    
    context = {
        'applications': applications,
        'total_count': applications.count(),
        'draft_count': applications.filter(status='DRAFT').count(),
        'submitted_count': applications.filter(status='SUBMITTED').count(),
        'under_review_count': applications.filter(status='UNDER_REVIEW').count(),
        'approved_count': applications.filter(status='APPROVED').count(),
        'rejected_count': applications.filter(status='REJECTED').count(),
        'revision_requested_count': applications.filter(status='REVISION_REQUESTED').count(),
    }
    
    return render(request, 'users/applicant_dashboard.html', context)


@reviewer_required
def reviewer_dashboard(request):
    """Dashboard for reviewers with comprehensive assignment tracking."""
    from apps.reviews.models import ReviewAssignment
    
    assignments = ReviewAssignment.objects.filter(
        reviewer=request.user
    ).select_related('application', 'rubric').order_by('-assigned_date')
    
    context = {
        'assignments': assignments,
        'total_count': assignments.count(),
        'pending_count': assignments.filter(status='ASSIGNED').count(),
        'in_progress_count': assignments.filter(status='IN_PROGRESS').count(),
        'completed_count': assignments.filter(status='COMPLETED').count(),
    }
    
    return render(request, 'users/reviewer_dashboard.html', context)


@admin_required
def admin_dashboard(request):
    """Dashboard for administrators."""
    from apps.applications.models import Application
    from apps.reviews.models import ReviewAssignment
    from django.db.models import Count, Avg
    
    # Application statistics
    applications = Application.objects.all()
    app_stats = applications.values('status').annotate(count=Count('id'))
    
    # Reviewer load statistics
    reviewers = User.objects.filter(role=User.Role.REVIEWER).order_by('-current_load')
    
    # Recent activity
    recent_applications = applications.order_by('-updated_at')[:10]
    
    context = {
        'app_stats': app_stats,
        'total_applications': applications.count(),
        'reviewers': reviewers,
        'recent_applications': recent_applications,
    }
    
    return render(request, 'users/admin_dashboard.html', context)


@login_required
def profile(request):
    """User profile view."""
    return render(request, 'users/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    """Edit profile view for all user types."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    # Determine if expertise_tags field should be shown (only for reviewers)
    show_expertise = request.user.role == 'REVIEWER'
    
    context = {
        'form': form,
        'show_expertise': show_expertise,
    }
    return render(request, 'users/edit_profile.html', context)


@admin_required
def user_list(request):
    """Admin view to list and manage all users."""
    users = User.objects.all().order_by('-date_joined')
    
    # Filter by role if requested
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'role_choices': User.Role.choices,
        'total_users': User.objects.count(),
        'applicant_count': User.objects.filter(role='APPLICANT').count(),
        'reviewer_count': User.objects.filter(role='REVIEWER').count(),
        'admin_count': User.objects.filter(role='ADMIN').count(),
    }
    
    return render(request, 'users/user_list.html', context)


@admin_required
def user_edit(request, user_id):
    """Admin view to edit a user's role and details."""
    from django.shortcuts import get_object_or_404
    
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in [choice[0] for choice in User.Role.choices]:
            old_role = user.role
            user.role = new_role
            
            # Update Django permissions based on role
            if new_role == 'ADMIN':
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            
            user.save()
            messages.success(request, f"User '{user.username}' role changed from {old_role} to {new_role}.")
        else:
            messages.error(request, "Invalid role selected.")
        
        return redirect('user_list')
    
    context = {
        'edit_user': user,
        'role_choices': User.Role.choices,
    }
    
    return render(request, 'users/user_edit.html', context)


@admin_required
def user_detail(request, user_id):
    """Admin view to see detailed user information."""
    from django.shortcuts import get_object_or_404
    from apps.applications.models import Application
    from apps.reviews.models import ReviewAssignment
    
    user = get_object_or_404(User, pk=user_id)
    
    context = {
        'view_user': user,
        'applications': Application.objects.filter(applicant=user) if user.is_applicant() else None,
        'assignments': ReviewAssignment.objects.filter(reviewer=user) if user.is_reviewer() else None,
    }
    
    return render(request, 'users/user_detail.html', context)
