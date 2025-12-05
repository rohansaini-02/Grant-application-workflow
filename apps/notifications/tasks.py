"""
Cron tasks for notifications and reminders.
"""

from django.utils import timezone
from datetime import timedelta
from apps.reviews.models import ReviewAssignment
from apps.applications.models import Application, DeadlineRule
from .services import EmailService, NotificationService
from .models import Notification


def send_deadline_reminders():
    """
    Send reminders for upcoming deadlines.
    Runs daily via django-crontab.
    """
    print(f"[{timezone.now()}] Running deadline reminders...")
    
    # Get all active deadline rules
    rules = DeadlineRule.objects.filter(is_active=True)
    
    for rule in rules:
        for days_before in rule.reminder_days_before:
            # Calculate target deadline date
            target_date = timezone.now() + timedelta(days=days_before)
            
            # Find applications with deadlines on target date
            applications = Application.objects.filter(
                status__in=rule.applies_to_statuses,
                deadline__date=target_date.date()
            )
            
            for app in applications:
                # Send notification to applicant
                NotificationService.create_notification(
                    recipient=app.applicant,
                    title=f"Deadline Reminder: {days_before} days",
                    message=f"Your application '{app.title}' deadline is in {days_before} days.",
                    notification_type=Notification.NotificationType.REMINDER,
                    link_url=f"/applications/{app.id}/"
                )
    
    # Send review reminders
    upcoming_reviews = ReviewAssignment.objects.filter(
        status=ReviewAssignment.AssignmentStatus.ASSIGNED,
        due_date__lte=timezone.now() + timedelta(days=3),
        due_date__gte=timezone.now()
    )
    
    for assignment in upcoming_reviews:
        days_remaining = (assignment.due_date - timezone.now()).days
        
        NotificationService.create_notification(
            recipient=assignment.reviewer,
            title=f"Review Due in {days_remaining} days",
            message=f"Your review for '{assignment.application.title}' is due soon.",
            notification_type=Notification.NotificationType.REMINDER,
            link_url=f"/reviews/{assignment.id}/"
        )
        
        # Send email reminder
        EmailService.send_review_reminder(assignment)
    
    print(f"[{timezone.now()}] Deadline reminders completed.")


def mark_overdue_items():
    """
    Mark overdue reviews and applications.
    Runs daily via django-crontab.
    """
    print(f"[{timezone.now()}] Marking overdue items...")
    
    # Find overdue review assignments
    overdue_reviews = ReviewAssignment.objects.filter(
        status=ReviewAssignment.AssignmentStatus.ASSIGNED,
        due_date__lt=timezone.now()
    )
    
    for assignment in overdue_reviews:
        NotificationService.create_notification(
            recipient=assignment.reviewer,
            title="Overdue Review",
            message=f"Your review for '{assignment.application.title}' is overdue.",
            notification_type=Notification.NotificationType.WARNING,
            link_url=f"/reviews/{assignment.id}/"
        )
    
    # Find overdue applications
    overdue_apps = Application.objects.filter(
        deadline__lt=timezone.now(),
        status__in=['DRAFT', 'UNDER_REVISION']
    )
    
    for app in overdue_apps:
        NotificationService.create_notification(
            recipient=app.applicant,
            title="Application Deadline Passed",
            message=f"The deadline for '{app.title}' has passed.",
            notification_type=Notification.NotificationType.ERROR,
            link_url=f"/applications/{app.id}/"
        )
    
    print(f"[{timezone.now()}] Overdue marking completed.")
