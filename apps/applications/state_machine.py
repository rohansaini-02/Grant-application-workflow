"""
State machine service for application workflow transitions.
Enforces valid transitions and creates audit logs.
"""

from django.utils import timezone
from .models import Application, ApplicationStatus, STATE_TRANSITIONS, AuditLog


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class ApplicationStateMachine:
    """
    Service class for managing application state transitions.
    """
    
    def __init__(self, application):
        self.application = application
    
    def can_transition_to(self, new_status):
        """Check if transition is allowed."""
        return self.application.can_transition_to(new_status)
    
    def transition_to(self, new_status, actor=None, reason='', ip_address=None):
        """
        Transition application to new status.
        
        Args:
            new_status: Target status (ApplicationStatus)
            actor: User performing the transition (can be None for system actions)
            reason: Reason for the transition
            ip_address: IP address of the actor
        
        Returns:
            The updated application
        
        Raises:
            StateTransitionError: If transition is not allowed
        """
        if not self.can_transition_to(new_status):
            raise StateTransitionError(
                f"Cannot transition from {self.application.status} to {new_status}. "
                f"Allowed transitions: {STATE_TRANSITIONS.get(self.application.status, [])}"
            )
        
        old_status = self.application.status
        self.application.status = new_status
        
        # Update submitted_at timestamp if transitioning to SUBMITTED
        if new_status == ApplicationStatus.SUBMITTED and not self.application.submitted_at:
            self.application.submitted_at = timezone.now()
        
        self.application.save(update_fields=['status', 'submitted_at', 'updated_at'])
        
        # Create audit log
        self._create_audit_log(
            old_status=old_status,
            new_status=new_status,
            actor=actor,
            reason=reason,
            ip_address=ip_address
        )
        
        return self.application
    
    def _create_audit_log(self, old_status, new_status, actor, reason, ip_address):
        """Create audit log entry for state transition."""
        AuditLog.objects.create(
            actor=actor,
            application=self.application,
            action_type=AuditLog.ActionType.STATE_CHANGE,
            details={
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason,
            },
            ip_address=ip_address
        )
    
    def get_allowed_transitions(self):
        """Get list of allowed transitions from current state."""
        return STATE_TRANSITIONS.get(self.application.status, [])
    
    def get_transition_history(self):
        """Get all state transitions for this application."""
        return AuditLog.objects.filter(
            application=self.application,
            action_type=AuditLog.ActionType.STATE_CHANGE
        ).order_by('-timestamp')


def create_audit_log(action_type, actor=None, application=None, details=None, ip_address=None):
    """
    Utility function to create audit log entries.
    
    Args:
        action_type: Type of action (AuditLog.ActionType)
        actor: User performing the action (optional)
        application: Related application (optional)
        details: Dictionary of action details
        ip_address: IP address of the actor
    
    Returns:
        Created AuditLog instance
    """
    return AuditLog.objects.create(
        actor=actor,
        application=application,
        action_type=action_type,
        details=details or {},
        ip_address=ip_address
    )
