"""
Permission utilities for role-based and object-level access control.
Integrates with Django's permission system through role-based groups.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """
    Decorator to require specific user roles.
    Also checks Django permissions if the user has them through their role-based group.
    
    Usage:
        @role_required('ADMIN', 'REVIEWER')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return redirect('login')
            
            # Check if user has the required role
            if request.user.role not in roles:
                raise PermissionDenied("You do not have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(perm_codename):
    """
    Decorator to require a specific Django permission.
    Checks both direct user permissions and group-based permissions.
    
    Usage:
        @permission_required('applications.view_application')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return redirect('login')
            
            # Check Django permission (includes group permissions)
            if not request.user.has_perm(perm_codename):
                raise PermissionDenied("You do not have the required permission.")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def role_or_permission_required(roles=None, perms=None):
    """
    Decorator that requires either a specific role OR a specific permission.
    Useful for flexible access control.
    
    Usage:
        @role_or_permission_required(roles=['ADMIN'], perms=['applications.view_application'])
        def my_view(request):
            ...
    """
    roles = roles or []
    perms = perms or []
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return redirect('login')
            
            # Check role
            has_role = request.user.role in roles if roles else False
            
            # Check permissions
            has_perm = any(request.user.has_perm(p) for p in perms) if perms else False
            
            if not has_role and not has_perm:
                raise PermissionDenied("You do not have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def applicant_required(view_func):
    """Decorator to require APPLICANT role."""
    return role_required('APPLICANT')(view_func)


def reviewer_required(view_func):
    """Decorator to require REVIEWER role."""
    return role_required('REVIEWER')(view_func)


def admin_required(view_func):
    """Decorator to require ADMIN role."""
    return role_required('ADMIN')(view_func)


def can_view_application(user, application):
    """
    Check if user can view an application.
    
    Rules:
    - Applicant can view their own applications
    - Reviewer can view assigned applications
    - Admin can view all applications
    - Users with 'applications.view_application' permission can view all
    """
    # Check Django permission first
    if user.has_perm('applications.view_application'):
        return True
    
    if user.is_admin_user():
        return True
    
    if user.is_applicant() and application.applicant == user:
        return True
    
    if user.is_reviewer():
        return application.reviewassignment_set.filter(reviewer=user).exists()
    
    return False


def can_edit_application(user, application):
    """
    Check if user can edit an application.
    
    Rules:
    - Applicant can edit their own applications in DRAFT or UNDER_REVISION states
    - Admin can edit any application
    - Users with 'applications.change_application' permission can edit all
    """
    # Check Django permission first
    if user.has_perm('applications.change_application'):
        return True
    
    if user.is_admin_user():
        return True
    
    if user.is_applicant() and application.applicant == user:
        return application.status in ['DRAFT', 'UNDER_REVISION']
    
    return False


def can_review_application(user, application):
    """
    Check if user can review an application.
    
    Rules:
    - Reviewer must have an active assignment
    - Admin can review any application
    - Users with 'reviews.add_review' permission can review all
    """
    # Check Django permission first
    if user.has_perm('reviews.add_review'):
        return True
    
    if user.is_admin_user():
        return True
    
    if user.is_reviewer():
        return application.reviewassignment_set.filter(
            reviewer=user,
            status='ASSIGNED'
        ).exists()
    
    return False


def user_has_group_permission(user, perm_codename):
    """
    Check if user has a specific permission through their role-based group.
    
    Args:
        user: The user object
        perm_codename: The permission codename (e.g., 'view_application')
        
    Returns:
        bool: True if user has the permission through their group
    """
    if not user.is_authenticated:
        return False
    
    # Use Django's built-in permission check which includes group permissions
    return user.has_perm(perm_codename)
