"""
Review models for Grant Application Workflow.
Implements rubric-based scoring, reviewer assignments, COI flagging, and blinding.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Rubric(models.Model):
    """
    Scoring rubric template with multiple criteria.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Rubric name"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Rubric description and instructions"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rubric is currently in use"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_total_weight(self):
        """Calculate total weight of all criteria."""
        return sum(c.weight for c in self.criteria.all())
    
    def calculate_weighted_score(self, scores_dict):
        """
        Calculate weighted score from criterion scores.
        
        Args:
            scores_dict: Dictionary {criterion_id: score}
        
        Returns:
            Weighted total score (0-100)
        """
        from decimal import Decimal
        
        total_weight = self.get_total_weight()
        if total_weight == 0:
            return Decimal('0')
        
        weighted_sum = Decimal('0')
        for criterion in self.criteria.all():
            score = Decimal(str(scores_dict.get(str(criterion.id), 0)))
            max_score = Decimal(str(criterion.max_score))
            weighted_sum += (score / max_score) * criterion.weight
        
        return (weighted_sum / total_weight) * Decimal('100')


class Criterion(models.Model):
    """
    Individual scoring criterion within a rubric.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    rubric = models.ForeignKey(
        Rubric,
        on_delete=models.CASCADE,
        related_name='criteria'
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Criterion name"
    )
    
    description = models.TextField(
        help_text="Detailed description and scoring guidelines"
    )
    
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Weight of this criterion in overall score"
    )
    
    min_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum possible score"
    )
    
    max_score = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Maximum possible score"
    )
    
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this criterion must be scored"
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Display order"
    )
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ['rubric', 'name']
    
    def __str__(self):
        return f"{self.rubric.name} - {self.name}"


class ReviewAssignment(models.Model):
    """
    Assignment of a reviewer to an application.
    """
    
    class AssignmentStatus(models.TextChoices):
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        DECLINED = 'DECLINED', 'Declined'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='review_assignments'
    )
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_assignments',
        limit_choices_to={'role': 'REVIEWER'}
    )
    
    rubric = models.ForeignKey(
        Rubric,
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.ASSIGNED,
        db_index=True
    )
    
    is_blinded = models.BooleanField(
        default=True,
        help_text="Whether reviewer sees blinded application (PI/team hidden)"
    )
    
    assigned_date = models.DateTimeField(auto_now_add=True, db_index=True)
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Review due date"
    )
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made'
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Admin notes about this assignment"
    )
    
    class Meta:
        ordering = ['-assigned_date']
        unique_together = ['application', 'reviewer']
        indexes = [
            models.Index(fields=['reviewer', 'status']),
            models.Index(fields=['application', 'status']),
        ]
    
    def __str__(self):
        return f"{self.reviewer.get_full_name()} → {self.application.title}"
    
    def is_overdue(self):
        """Check if review is past due date."""
        if self.due_date and self.status != self.AssignmentStatus.COMPLETED:
            return timezone.now() > self.due_date
        return False


class Review(models.Model):
    """
    Reviewer's evaluation of an application.
    """
    
    class ReviewStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    assignment = models.OneToOneField(
        ReviewAssignment,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    # Scores stored as JSON: {criterion_id: score}
    scores = models.JSONField(
        default=dict,
        help_text="Dictionary mapping criterion IDs to scores"
    )
    
    # Cached overall score for querying
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="Weighted overall score (0-100)"
    )
    
    # Comments
    strengths = models.TextField(
        blank=True,
        help_text="Application strengths"
    )
    
    weaknesses = models.TextField(
        blank=True,
        help_text="Application weaknesses"
    )
    
    recommendation = models.TextField(
        blank=True,
        help_text="Overall recommendation"
    )
    
    confidential_comments = models.TextField(
        blank=True,
        help_text="Comments visible only to admins (not shared with applicant)"
    )
    
    # Status and timestamps
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.DRAFT,
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at', '-updated_at']
    
    def __str__(self):
        return f"Review by {self.assignment.reviewer.get_full_name()} - {self.status}"
    
    def calculate_overall_score(self):
        """Calculate and cache overall weighted score."""
        rubric = self.assignment.rubric
        self.overall_score = rubric.calculate_weighted_score(self.scores)
        return self.overall_score
    
    def is_complete(self):
        """Check if all required criteria are scored."""
        rubric = self.assignment.rubric
        required_criteria = rubric.criteria.filter(is_required=True)
        
        for criterion in required_criteria:
            if str(criterion.id) not in self.scores:
                return False
        
        return True
    
    def submit(self):
        """Submit the review (mark as submitted)."""
        if not self.is_complete():
            raise ValueError("Cannot submit incomplete review. All required criteria must be scored.")
        
        self.status = self.ReviewStatus.SUBMITTED
        self.submitted_at = timezone.now()
        self.calculate_overall_score()
        self.save()
        
        # Update assignment status
        self.assignment.status = ReviewAssignment.AssignmentStatus.COMPLETED
        self.assignment.save()
        
        # Update application status to REVIEWED if all reviews are completed
        from apps.applications.models import ApplicationStatus
        application = self.assignment.application
        all_assignments = application.review_assignments.all()
        completed_count = all_assignments.filter(status=ReviewAssignment.AssignmentStatus.COMPLETED).count()
        
        # If all assignments are completed, mark application as Reviewed
        if completed_count == all_assignments.count() and all_assignments.count() > 0:
            application.status = ApplicationStatus.REVIEWED
            application.save()


class COIFlag(models.Model):
    """
    Conflict of Interest declaration.
    """
    
    class COIType(models.TextChoices):
        FINANCIAL = 'FINANCIAL', 'Financial Conflict'
        PERSONAL = 'PERSONAL', 'Personal Relationship'
        PROFESSIONAL = 'PROFESSIONAL', 'Professional Relationship'
        INSTITUTIONAL = 'INSTITUTIONAL', 'Institutional Conflict'
        OTHER = 'OTHER', 'Other'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coi_flags'
    )
    
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='coi_flags'
    )
    
    coi_type = models.CharField(
        max_length=20,
        choices=COIType.choices
    )
    
    description = models.TextField(
        help_text="Description of the conflict of interest"
    )
    
    declared_at = models.DateTimeField(auto_now_add=True)
    
    is_resolved = models.BooleanField(
        default=False,
        help_text="Whether admin has addressed this COI"
    )
    
    resolution_notes = models.TextField(
        blank=True,
        help_text="Admin notes on how COI was resolved"
    )
    
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_cois'
    )
    
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-declared_at']
        unique_together = ['reviewer', 'application']
    
    def __str__(self):
        return f"COI: {self.reviewer.get_full_name()} - {self.application.title}"
    
    def resolve(self, resolved_by, resolution_notes=''):
        """Mark COI as resolved."""
        self.is_resolved = True
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.save()


class CalibrationSession(models.Model):
    """
    Calibration session for reviewers to practice scoring and reach consensus.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(
        max_length=255,
        help_text="Session name"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Session description and objectives"
    )
    
    example_application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='calibration_sessions',
        help_text="Example application for scoring practice"
    )
    
    rubric = models.ForeignKey(
        Rubric,
        on_delete=models.PROTECT,
        related_name='calibration_sessions'
    )
    
    # Consensus score (set by admin after discussion)
    consensus_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Agreed-upon consensus score"
    )
    
    consensus_scores_detail = models.JSONField(
        default=dict,
        blank=True,
        help_text="Consensus scores per criterion {criterion_id: score}"
    )
    
    session_date = models.DateTimeField(
        help_text="When the calibration session takes place"
    )
    
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='calibration_sessions',
        limit_choices_to={'role': 'REVIEWER'},
        help_text="Reviewers participating in this session"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_calibrations'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_completed = models.BooleanField(
        default=False,
        help_text="Whether the session has been completed"
    )
    
    discussion_notes = models.TextField(
        blank=True,
        help_text="Notes from the calibration discussion"
    )
    
    class Meta:
        ordering = ['-session_date']
    
    def __str__(self):
        return f"{self.name} - {self.session_date.strftime('%Y-%m-%d')}"
    
    def get_participant_scores(self):
        """Get all individual scores from participants."""
        return CalibrationScore.objects.filter(session=self)


class CalibrationScore(models.Model):
    """
    Individual reviewer's score during a calibration session.
    """
    
    session = models.ForeignKey(
        CalibrationSession,
        on_delete=models.CASCADE,
        related_name='individual_scores'
    )
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calibration_scores'
    )
    
    scores = models.JSONField(
        default=dict,
        help_text="Reviewer's scores {criterion_id: score}"
    )
    
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    comments = models.TextField(
        blank=True,
        help_text="Reviewer's comments on their scoring"
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'reviewer']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.reviewer.get_full_name()} - {self.session.name}"
