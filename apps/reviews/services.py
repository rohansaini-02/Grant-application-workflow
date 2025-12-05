"""
Services for reviewer assignment, load balancing, and COI detection.
"""

from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import ReviewAssignment, Review, COIFlag, Rubric
from apps.users.models import User
from apps.applications.state_machine import create_audit_log
from apps.applications.models import AuditLog


class ReviewerAssignmentService:
    """
    Service for intelligent reviewer assignment with load balancing and expertise matching.
    """
    
    @staticmethod
    def get_recommended_reviewers(application, rubric, num_recommendations=5):
        """
        Get recommended reviewers for an application based on expertise and load.
        
        Args:
            application: Application instance
            rubric: Rubric to use for review
            num_recommendations: Number of reviewers to recommend
        
        Returns:
            QuerySet of recommended User instances with annotation
        """
        # Get all active reviewers
        reviewers = User.objects.filter(
            role=User.Role.REVIEWER,
            is_active=True
        )
        
        # Exclude reviewers with COI
        reviewers_with_coi = COIFlag.objects.filter(
            application=application
        ).values_list('reviewer_id', flat=True)
        reviewers = reviewers.exclude(id__in=reviewers_with_coi)
        
        # Exclude reviewers already assigned to this application
        already_assigned = ReviewAssignment.objects.filter(
            application=application
        ).values_list('reviewer_id', flat=True)
        reviewers = reviewers.exclude(id__in=already_assigned)
        
        # Calculate expertise match score
        app_tags = set(application.tags)
        
        scored_reviewers = []
        for reviewer in reviewers:
            reviewer_tags = set(reviewer.expertise_tags)
            
            # Calculate Jaccard similarity for expertise matching
            if app_tags and reviewer_tags:
                intersection = len(app_tags & reviewer_tags)
                union = len(app_tags | reviewer_tags)
                expertise_score = intersection / union if union > 0 else 0
            else:
                expertise_score = 0
            
            # Load balancing: prefer reviewers with lower current load
            # Normalize load (assuming max load of 20)
            load_score = 1 - (min(reviewer.current_load, 20) / 20)
            
            # Combined score (60% expertise, 40% load balance)
            combined_score = (expertise_score * 0.6) + (load_score * 0.4)
            
            scored_reviewers.append({
                'reviewer': reviewer,
                'expertise_score': expertise_score,
                'load_score': load_score,
                'combined_score': combined_score,
                'current_load': reviewer.current_load,
            })
        
        # Sort by combined score (descending)
        scored_reviewers.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return scored_reviewers[:num_recommendations]
    
    @staticmethod
    def assign_reviewer(application, reviewer, rubric, assigned_by, due_days=14, is_blinded=True, notes=''):
        """
        Assign a reviewer to an application.
        
        Args:
            application: Application instance
            reviewer: User instance (reviewer)
            rubric: Rubric instance
            assigned_by: User who made the assignment
            due_days: Number of days until review is due
            is_blinded: Whether to blind the review
            notes: Admin notes
        
        Returns:
            Tuple (ReviewAssignment or None, error_message or None)
        """
        # Check if reviewer has COI
        if COIFlag.objects.filter(application=application, reviewer=reviewer).exists():
            return None, "Reviewer has declared a conflict of interest for this application."
        
        # Check if already assigned
        if ReviewAssignment.objects.filter(application=application, reviewer=reviewer).exists():
            return None, "Reviewer is already assigned to this application."
        
        # Create assignment
        due_date = timezone.now() + timedelta(days=due_days)
        
        assignment = ReviewAssignment.objects.create(
            application=application,
            reviewer=reviewer,
            rubric=rubric,
            assigned_by=assigned_by,
            due_date=due_date,
            is_blinded=is_blinded,
            notes=notes
        )
        
        # Increment reviewer load
        reviewer.increment_load()
        
        # Create audit log
        create_audit_log(
            action_type=AuditLog.ActionType.REVIEW_ASSIGNED,
            actor=assigned_by,
            application=application,
            details={
                'reviewer_id': str(reviewer.id),
                'reviewer_name': reviewer.get_full_name() or reviewer.username,
                'rubric': rubric.name,
                'due_date': due_date.isoformat(),
                'is_blinded': is_blinded
            }
        )
        
        return assignment, None
    
    @staticmethod
    def bulk_assign_reviewers(application, reviewer_ids, rubric, assigned_by, due_days=14, is_blinded=True):
        """
        Assign multiple reviewers to an application.
        
        Args:
            application: Application instance
            reviewer_ids: List of reviewer user IDs
            rubric: Rubric instance
            assigned_by: User who made the assignments
            due_days: Number of days until reviews are due
            is_blinded: Whether to blind the reviews
        
        Returns:
            Tuple (list of assignments, list of errors)
        """
        assignments = []
        errors = []
        
        for reviewer_id in reviewer_ids:
            try:
                reviewer = User.objects.get(id=reviewer_id, role=User.Role.REVIEWER)
                assignment, error = ReviewerAssignmentService.assign_reviewer(
                    application=application,
                    reviewer=reviewer,
                    rubric=rubric,
                    assigned_by=assigned_by,
                    due_days=due_days,
                    is_blinded=is_blinded
                )
                
                if assignment:
                    assignments.append(assignment)
                else:
                    errors.append(f"{reviewer.username}: {error}")
            
            except User.DoesNotExist:
                errors.append(f"Reviewer ID {reviewer_id} not found")
        
        return assignments, errors
    
    @staticmethod
    def unassign_reviewer(assignment, unassigned_by, reason=''):
        """
        Remove a reviewer assignment.
        
        Args:
            assignment: ReviewAssignment instance
            unassigned_by: User who removed the assignment
            reason: Reason for removal
        """
        application = assignment.application
        reviewer = assignment.reviewer
        
        # Decrement reviewer load
        reviewer.decrement_load()
        
        # Create audit log before deletion
        create_audit_log(
            action_type=AuditLog.ActionType.OTHER,
            actor=unassigned_by,
            application=application,
            details={
                'action': 'reviewer_unassigned',
                'reviewer_id': str(reviewer.id),
                'reviewer_name': reviewer.get_full_name() or reviewer.username,
                'reason': reason
            }
        )
        
        # Delete assignment (cascade will delete review if exists)
        assignment.delete()


class COIService:
    """Service for COI management."""
    
    @staticmethod
    def declare_coi(reviewer, application, coi_type, description):
        """
        Declare a conflict of interest.
        
        Args:
            reviewer: User instance (reviewer)
            application: Application instance
            coi_type: COIFlag.COIType
            description: Description of the conflict
        
        Returns:
            COIFlag instance
        """
        coi_flag = COIFlag.objects.create(
            reviewer=reviewer,
            application=application,
            coi_type=coi_type,
            description=description
        )
        
        # Remove any existing assignment
        try:
            assignment = ReviewAssignment.objects.get(
                application=application,
                reviewer=reviewer
            )
            ReviewerAssignmentService.unassign_reviewer(
                assignment=assignment,
                unassigned_by=reviewer,
                reason=f"COI declared: {coi_type}"
            )
        except ReviewAssignment.DoesNotExist:
            pass
        
        return coi_flag
    
    @staticmethod
    def check_potential_coi(reviewer, application):
        """
        Check for potential COI indicators.
        
        Args:
            reviewer: User instance
            application: Application instance
        
        Returns:
            List of potential COI warnings
        """
        warnings = []
        
        # Check if reviewer and applicant share organization
        if reviewer.organization and reviewer.organization == application.applicant.organization:
            warnings.append("Same organization as applicant")
        
        # Check if reviewer has reviewed other applications from same applicant
        previous_reviews = ReviewAssignment.objects.filter(
            reviewer=reviewer,
            application__applicant=application.applicant
        ).exclude(application=application)
        
        if previous_reviews.exists():
            warnings.append(f"Previously reviewed {previous_reviews.count()} applications from this applicant")
        
        return warnings


class ScoringService:
    """Service for score calculations and analytics."""
    
    @staticmethod
    def calculate_application_statistics(application):
        """
        Calculate scoring statistics for an application.
        
        Args:
            application: Application instance
        
        Returns:
            Dictionary of statistics
        """
        reviews = Review.objects.filter(
            assignment__application=application,
            status=Review.ReviewStatus.SUBMITTED
        )
        
        if not reviews.exists():
            return {
                'review_count': 0,
                'mean_score': None,
                'min_score': None,
                'max_score': None,
                'std_dev': None,
            }
        
        scores = [float(r.overall_score) for r in reviews if r.overall_score is not None]
        
        if not scores:
            return {'review_count': reviews.count(), 'mean_score': None}
        
        mean_score = sum(scores) / len(scores)
        
        # Calculate standard deviation
        if len(scores) > 1:
            variance = sum((x - mean_score) ** 2 for x in scores) / (len(scores) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
        
        return {
            'review_count': len(scores),
            'mean_score': mean_score,
            'min_score': min(scores),
            'max_score': max(scores),
            'std_dev': std_dev,
        }
    
    @staticmethod
    def calculate_criterion_statistics(rubric, applications=None):
        """
        Calculate per-criterion statistics across reviews.
        
        Args:
            rubric: Rubric instance
            applications: Optional queryset of applications to limit analysis
        
        Returns:
            Dictionary mapping criterion IDs to statistics
        """
        # Get all submitted reviews for this rubric
        reviews_query = Review.objects.filter(
            assignment__rubric=rubric,
            status=Review.ReviewStatus.SUBMITTED
        )
        
        if applications:
            reviews_query = reviews_query.filter(assignment__application__in=applications)
        
        criterion_stats = {}
        
        for criterion in rubric.criteria.all():
            criterion_id = str(criterion.id)
            scores = []
            
            for review in reviews_query:
                if criterion_id in review.scores:
                    scores.append(review.scores[criterion_id])
            
            if scores:
                mean_score = sum(scores) / len(scores)
                
                if len(scores) > 1:
                    variance = sum((x - mean_score) ** 2 for x in scores) / (len(scores) - 1)
                    std_dev = variance ** 0.5
                else:
                    std_dev = 0
                
                criterion_stats[criterion_id] = {
                    'criterion_name': criterion.name,
                    'count': len(scores),
                    'mean': mean_score,
                    'min': min(scores),
                    'max': max(scores),
                    'std_dev': std_dev,
                }
        
        return criterion_stats
