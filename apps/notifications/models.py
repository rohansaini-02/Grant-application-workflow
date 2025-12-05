"""
Notification models for Grant Application Workflow.
Implements in-app notifications and editable email templates.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    In-app notification for users.
    """
    
    class NotificationType(models.TextChoices):
        INFO = 'INFO', 'Information'
        SUCCESS = 'SUCCESS', 'Success'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        REMINDER = 'REMINDER', 'Reminder'
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Optional link to related object
    link_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL to navigate to when notification is clicked"
    )
    
    is_read = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class EmailTemplate(models.Model):
    """
    Editable email templates stored in database.
    """
    
    class TemplateType(models.TextChoices):
        APPLICATION_SUBMITTED = 'APPLICATION_SUBMITTED', 'Application Submitted'
        REVIEW_ASSIGNED = 'REVIEW_ASSIGNED', 'Review Assigned'
        REVIEW_REMINDER = 'REVIEW_REMINDER', 'Review Reminder'
        REVIEW_OVERDUE = 'REVIEW_OVERDUE', 'Review Overdue'
        DECISION_APPROVED = 'DECISION_APPROVED', 'Decision - Approved'
        DECISION_REJECTED = 'DECISION_REJECTED', 'Decision - Rejected'
        REVISION_REQUESTED = 'REVISION_REQUESTED', 'Revision Requested'
        DEADLINE_REMINDER = 'DEADLINE_REMINDER', 'Deadline Reminder'
        COI_DECLARED = 'COI_DECLARED', 'COI Declared'
        CUSTOM = 'CUSTOM', 'Custom'
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Template name for identification"
    )
    
    template_type = models.CharField(
        max_length=50,
        choices=TemplateType.choices,
        db_index=True
    )
    
    subject = models.CharField(
        max_length=255,
        help_text="Email subject line (supports template variables)"
    )
    
    body = models.TextField(
        help_text="Email body (supports template variables like {{applicant_name}}, {{application_title}}, etc.)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is currently in use"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render(self, context):
        """
        Render template with context variables.
        
        Args:
            context: Dictionary of template variables
        
        Returns:
            Tuple (rendered_subject, rendered_body)
        """
        rendered_subject = self.subject
        rendered_body = self.body
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered_subject = rendered_subject.replace(placeholder, str(value))
            rendered_body = rendered_body.replace(placeholder, str(value))
        
        return rendered_subject, rendered_body
