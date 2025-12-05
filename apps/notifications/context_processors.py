"""
Context processor for notifications.
"""

from .models import Notification


def notifications(request):
    """
    Add unread notifications to template context.
    """
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )[:10]  # Limit to 10 most recent
        
        return {
            'unread_notifications': unread_notifications,
            'unread_count': unread_notifications.count(),
        }
    
    return {
        'unread_notifications': [],
        'unread_count': 0,
    }
