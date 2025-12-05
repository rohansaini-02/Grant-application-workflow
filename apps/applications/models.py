"""
Application models for Grant Application Workflow.
Implements state machine, versioning, document management, and audit logging.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
import os
import uuid


class ApplicationStatus(models.TextChoices):
    """Application workflow states."""
    DRAFT = 'DRAFT', 'Draft'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    IN_TRIAGE = 'IN_TRIAGE', 'In Triage'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    REVIEWED = 'REVIEWED', 'Reviewed'
    DECISION_PENDING = 'DECISION_PENDING', 'Decision Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    REVISION_REQUESTED = 'REVISION_REQUESTED', 'Revision Requested'
    UNDER_REVISION = 'UNDER_REVISION', 'Under Revision'
    APPEAL_PENDING = 'APPEAL_PENDING', 'Appeal Pending'
    APPEAL_REVIEWED = 'APPEAL_REVIEWED', 'Appeal Reviewed'
    ARCHIVED = 'ARCHIVED', 'Archived'


# State machine transitions
STATE_TRANSITIONS = {
    ApplicationStatus.DRAFT: [ApplicationStatus.SUBMITTED],
    ApplicationStatus.SUBMITTED: [ApplicationStatus.IN_TRIAGE, ApplicationStatus.DRAFT],
    ApplicationStatus.IN_TRIAGE: [ApplicationStatus.ASSIGNED, ApplicationStatus.REJECTED],
    ApplicationStatus.ASSIGNED: [ApplicationStatus.UNDER_REVIEW],
    ApplicationStatus.UNDER_REVIEW: [ApplicationStatus.REVIEWED],
    ApplicationStatus.REVIEWED: [ApplicationStatus.DECISION_PENDING],
    ApplicationStatus.DECISION_PENDING: [
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.REVISION_REQUESTED
    ],
    ApplicationStatus.APPROVED: [ApplicationStatus.ARCHIVED],
    ApplicationStatus.REJECTED: [ApplicationStatus.APPEAL_PENDING, ApplicationStatus.ARCHIVED],
    ApplicationStatus.REVISION_REQUESTED: [ApplicationStatus.UNDER_REVISION],
    ApplicationStatus.UNDER_REVISION: [ApplicationStatus.SUBMITTED],
    ApplicationStatus.APPEAL_PENDING: [ApplicationStatus.APPEAL_REVIEWED],
    ApplicationStatus.APPEAL_REVIEWED: [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED],
    ApplicationStatus.ARCHIVED: [],
}


class Call(models.Model):
    """
    Call for Proposals - represents a funding opportunity.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(
        max_length=500,
        help_text="Call title"
    )
    
    description = models.TextField(
        help_text="Detailed description of the funding opportunity"
    )
    
    deadline = models.DateTimeField(
        help_text="Application submission deadline",
        db_index=True
    )
    
    is_open = models.BooleanField(
        default=True,
        help_text="Whether this call is currently accepting applications"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_calls'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata
    funding_amount_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum funding amount"
    )
    
    funding_amount_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum funding amount"
    )
    
    eligibility_criteria = models.TextField(
        blank=True,
        help_text="Who can apply"
    )
    
    class Meta:
        ordering = ['-deadline']
        indexes = [
            models.Index(fields=['is_open', '-deadline']),
        ]
    
    def __str__(self):
        return self.title
    
    def is_active(self):
        """Check if call is still open and not past deadline."""
        return self.is_open and timezone.now() < self.deadline
    
    def days_until_deadline(self):
        """Calculate days remaining until deadline."""
        if self.deadline:
            delta = self.deadline - timezone.now()
            return delta.days
        return None


class Application(models.Model):
    """
    Core application model with state machine.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to Call
    call = models.ForeignKey(
        Call,
        on_delete=models.CASCADE,
        related_name='applications',
        null=True,
        blank=True,
        help_text="The call this application is responding to"
    )
    
    # Applicant information
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        help_text="User who submitted the application"
    )
    
    # Application details
    title = models.CharField(
        max_length=500,
        help_text="Application title"
    )
    
    call_program = models.CharField(
        max_length=255,
        help_text="Grant call or program name",
        db_index=True
    )
    
    abstract = models.TextField(
        help_text="Brief abstract or summary"
    )
    
    requested_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Requested funding amount"
    )
    
    # State and workflow
    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        db_index=True,
        help_text="Current application status"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Application deadline"
    )
    
    # Metadata
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorization and matching (e.g., ['biology', 'climate'])"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['deadline']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def can_transition_to(self, new_status):
        """Check if transition to new_status is allowed."""
        allowed_transitions = STATE_TRANSITIONS.get(self.status, [])
        return new_status in allowed_transitions
    
    def get_current_version(self):
        """Get the most recent version of this application."""
        return self.versions.order_by('-version_number').first()
    
    def is_editable(self):
        """Check if application can be edited."""
        return self.status in [ApplicationStatus.DRAFT, ApplicationStatus.UNDER_REVISION]
    
    def is_overdue(self):
        """Check if application is past deadline."""
        if self.deadline:
            return timezone.now() > self.deadline
        return False


class ApplicationVersion(models.Model):
    """
    Versioned snapshot of application data.
    Stores structured data and maintains history.
    """
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    
    version_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Version number (incremental)"
    )
    
    # Structured application data
    data = models.JSONField(
        help_text="Complete application data snapshot"
    )
    
    # Version metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_versions'
    )
    
    change_summary = models.TextField(
        blank=True,
        help_text="Summary of changes in this version"
    )
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['application', 'version_number']
        indexes = [
            models.Index(fields=['application', '-version_number']),
        ]
    
    def __str__(self):
        return f"{self.application.title} - v{self.version_number}"
    
    def get_diff(self, other_version):
        """
        Compare this version with another version.
        Returns a dict of changes.
        """
        if not other_version:
            return {'changes': 'Initial version'}
        
        changes = {}
        for key in self.data.keys():
            if key not in other_version.data:
                changes[key] = {'status': 'added', 'new': self.data[key]}
            elif self.data[key] != other_version.data.get(key):
                changes[key] = {
                    'status': 'modified',
                    'old': other_version.data[key],
                    'new': self.data[key]
                }
        
        for key in other_version.data.keys():
            if key not in self.data:
                changes[key] = {'status': 'removed', 'old': other_version.data[key]}
        
        return changes


def document_upload_path(instance, filename):
    """Generate upload path for documents."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', str(instance.application.id), filename)


class Document(models.Model):
    """
    File uploads associated with applications.
    """
    
    class DocumentType(models.TextChoices):
        PROPOSAL = 'PROPOSAL', 'Proposal Document'
        BUDGET = 'BUDGET', 'Budget Document'
        CV = 'CV', 'Curriculum Vitae'
        LETTER = 'LETTER', 'Letter of Support'
        OTHER = 'OTHER', 'Other'
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    
    file = models.FileField(
        upload_to=document_upload_path,
        help_text="Uploaded document file"
    )
    
    filename = models.CharField(
        max_length=255,
        help_text="Original filename"
    )
    
    file_size = models.IntegerField(
        help_text="File size in bytes"
    )
    
    mime_type = models.CharField(
        max_length=100,
        help_text="MIME type of the file"
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.filename} ({self.get_document_type_display()})"
    
    def get_file_extension(self):
        """Get file extension."""
        return os.path.splitext(self.filename)[1].lower()


class DeadlineRule(models.Model):
    """
    Configurable deadline rules for automated reminders and escalations.
    """
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    # Reminder settings
    reminder_days_before = models.JSONField(
        default=list,
        help_text="Days before deadline to send reminders (e.g., [7, 3, 1])"
    )
    
    # Escalation settings
    auto_escalate = models.BooleanField(
        default=False,
        help_text="Automatically escalate state on deadline"
    )
    
    escalation_status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        blank=True,
        help_text="Status to transition to on deadline"
    )
    
    # Applicability
    applies_to_statuses = models.JSONField(
        default=list,
        help_text="List of statuses this rule applies to"
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AuditLog(models.Model):
    """
    Append-only audit trail for all application state changes and actions.
    """
    
    class ActionType(models.TextChoices):
        STATE_CHANGE = 'STATE_CHANGE', 'State Change'
        CREATED = 'CREATED', 'Created'
        UPDATED = 'UPDATED', 'Updated'
        DOCUMENT_UPLOADED = 'DOCUMENT_UPLOADED', 'Document Uploaded'
        DOCUMENT_DELETED = 'DOCUMENT_DELETED', 'Document Deleted'
        REVIEW_ASSIGNED = 'REVIEW_ASSIGNED', 'Review Assigned'
        REVIEW_SUBMITTED = 'REVIEW_SUBMITTED', 'Review Submitted'
        COMMENT_ADDED = 'COMMENT_ADDED', 'Comment Added'
        DECISION_MADE = 'DECISION_MADE', 'Decision Made'
        OTHER = 'OTHER', 'Other'
    
    # Who performed the action (nullable for system actions)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # What was affected
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    
    # Action details
    action_type = models.CharField(
        max_length=30,
        choices=ActionType.choices,
        db_index=True
    )
    
    details = models.JSONField(
        default=dict,
        help_text="Detailed information about the action"
    )
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # IP address for security
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['application', '-timestamp']),
            models.Index(fields=['actor', '-timestamp']),
        ]
    
    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f"{actor_name} - {self.get_action_type_display()} at {self.timestamp}"


class Appeal(models.Model):
    """
    Appeal filed by applicant against a rejection decision.
    """
    
    class AppealStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='appeals'
    )
    
    appellant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='filed_appeals'
    )
    
    reason = models.TextField(
        help_text="Reason for appeal"
    )
    
    supporting_documents = models.TextField(
        blank=True,
        help_text="References to supporting documents"
    )
    
    status = models.CharField(
        max_length=20,
        choices=AppealStatus.choices,
        default=AppealStatus.PENDING
    )
    
    filed_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_appeals'
    )
    
    outcome = models.TextField(
        blank=True,
        help_text="Admin decision on appeal"
    )
    
    class Meta:
        ordering = ['-filed_at']
    
    def __str__(self):
        return f"Appeal for {self.application.title} - {self.get_status_display()}"


class RevisionRequest(models.Model):
    """
    Request from admin for applicant to revise their application.
    """
    
    class RevisionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Revision'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='revision_requests'
    )
    
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_revisions'
    )
    
    changes_required = models.TextField(
        help_text="Specific changes that need to be made"
    )
    
    status = models.CharField(
        max_length=20,
        choices=RevisionStatus.choices,
        default=RevisionStatus.PENDING
    )
    
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    applicant_notes = models.TextField(
        blank=True,
        help_text="Applicant's notes on revisions made"
    )
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Revision for {self.application.title} - {self.get_status_display()}"
