"""
Django admin customization for Grant Application Workflow.
"""

from django.contrib import admin
from django.contrib.admin import AdminSite


class GrantWorkflowAdminSite(AdminSite):
    """Custom admin site with improved styling."""
    
    site_header = "Grant Application Workflow Administration"
    site_title = "Grant Workflow Admin"
    index_title = "Dashboard"
    
    def index(self, request, extra_context=None):
        """Override index to add stats counts."""
        from apps.applications.models import Application
        from apps.reviews.models import ReviewAssignment
        from apps.users.models import User
        from apps.notifications.models import Notification
        
        extra_context = extra_context or {}
        extra_context['app_count'] = Application.objects.count()
        extra_context['review_count'] = ReviewAssignment.objects.count()
        extra_context['user_count'] = User.objects.count()
        extra_context['notif_count'] = Notification.objects.filter(is_read=False).count()
        
        return super().index(request, extra_context=extra_context)
    
    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }


# Create custom admin site instance
admin_site = GrantWorkflowAdminSite(name='admin')
