"""
Notification and email services.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification, EmailTemplate


class NotificationService:
    """Service for creating in-app notifications."""
    
    @staticmethod
    def create_notification(recipient, title, message, notification_type=Notification.NotificationType.INFO, link_url=''):
        """
        Create an in-app notification.
        
        Args:
            recipient: User instance
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            link_url: Optional URL to link to
        
        Returns:
            Notification instance
        """
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url
        )
    
    @staticmethod
    def notify_application_submitted(application):
        """Notify applicant that application was submitted."""
        NotificationService.create_notification(
            recipient=application.applicant,
            title="Application Submitted",
            message=f"Your application '{application.title}' has been successfully submitted.",
            notification_type=Notification.NotificationType.SUCCESS,
            link_url=f"/applications/{application.id}/"
        )
    
    @staticmethod
    def notify_review_assigned(assignment):
        """Notify reviewer of new assignment."""
        NotificationService.create_notification(
            recipient=assignment.reviewer,
            title="New Review Assignment",
            message=f"You have been assigned to review '{assignment.application.title}'.",
            notification_type=Notification.NotificationType.INFO,
            link_url=f"/reviews/{assignment.id}/"
        )
    
    @staticmethod
    def notify_admins(title, message, notification_type=Notification.NotificationType.INFO, link_url=''):
        """Notify all admins."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(role=User.Role.ADMIN)
        
        for admin in admins:
            NotificationService.create_notification(
                recipient=admin,
                title=title,
                message=message,
                notification_type=notification_type,
                link_url=link_url
            )

    @staticmethod
    def notify_admin_application_submitted(application):
        """Notify admins of new application submission."""
        NotificationService.notify_admins(
            title="New Application Submitted",
            message=f"New application '{application.title}' submitted by {application.applicant.get_full_name()}.",
            notification_type=Notification.NotificationType.INFO,
            link_url=f"/applications/{application.id}/"
        )

    @staticmethod
    def notify_admin_review_completed(review):
        """Notify admins of completed review."""
        NotificationService.notify_admins(
            title="Review Completed",
            message=f"Review completed for '{review.assignment.application.title}' by {review.assignment.reviewer.get_full_name()}.",
            notification_type=Notification.NotificationType.SUCCESS,
            link_url=f"/reviews/{review.assignment.id}/"
        )

    @staticmethod
    def notify_admin_coi_declared(coi_flag):
        """Notify admins of COI declaration."""
        NotificationService.notify_admins(
            title="Conflict of Interest Declared",
            message=f"COI declared by {coi_flag.reviewer.get_full_name()} for '{coi_flag.application.title}'.",
            notification_type=Notification.NotificationType.WARNING,
            link_url=f"/admin/reviews/coiflag/{coi_flag.id}/change/"
        )


class EmailService:
    """Service for sending emails using templates."""
    
    @staticmethod
    def send_email(template_name, recipient_email, context):
        """
        Send email using a template.
        
        Args:
            template_name: Name of the EmailTemplate
            recipient_email: Recipient email address
            context: Dictionary of template variables
        
        Returns:
            Boolean indicating success
        """
        try:
            template = EmailTemplate.objects.get(name=template_name, is_active=True)
            subject, body = template.render(context)
            
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            return True
        
        except EmailTemplate.DoesNotExist:
            print(f"Email template '{template_name}' not found")
            return False
        
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    @staticmethod
    def send_review_reminder(assignment):
        """Send reminder email to reviewer."""
        context = {
            'reviewer_name': assignment.reviewer.get_full_name() or assignment.reviewer.username,
            'application_title': assignment.application.title,
            'due_date': assignment.due_date.strftime('%Y-%m-%d') if assignment.due_date else 'N/A',
        }
        
        return EmailService.send_email(
            template_name='Review Reminder',
            recipient_email=assignment.reviewer.email,
            context=context
        )
