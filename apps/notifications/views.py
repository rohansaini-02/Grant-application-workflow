"""
Views for notifications app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notification_list(request):
    """List all notifications for current user."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    return render(request, 'notifications/list.html', {
        'notifications': notifications
    })


@login_required
def mark_as_read(request, pk):
    """Mark notification as read."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()
    
    if notification.link_url:
        return redirect(notification.link_url)
    
    return redirect('notifications:list')


@login_required
def mark_all_as_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return redirect('notifications:list')
