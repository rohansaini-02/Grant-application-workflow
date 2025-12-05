"""
Basic tests for Grant Application Workflow.
"""

import pytest
from django.test import TestCase
from apps.users.models import User
from apps.applications.models import Application, ApplicationStatus
from apps.applications.state_machine import ApplicationStateMachine, StateTransitionError


class UserModelTest(TestCase):
    """Tests for User model."""
    
    def test_create_user(self):
        """Test user creation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=User.Role.APPLICANT
        )
        
        assert user.username == 'testuser'
        assert user.is_applicant()
        assert not user.is_reviewer()
        assert not user.is_admin_user()
    
    def test_reviewer_load(self):
        """Test reviewer load tracking."""
        reviewer = User.objects.create_user(
            username='reviewer',
            role=User.Role.REVIEWER
        )
        
        assert reviewer.current_load == 0
        
        reviewer.increment_load()
        assert reviewer.current_load == 1
        
        reviewer.decrement_load()
        assert reviewer.current_load == 0


class ApplicationStateMachineTest(TestCase):
    """Tests for application state machine."""
    
    def setUp(self):
        """Set up test data."""
        self.applicant = User.objects.create_user(
            username='applicant',
            role=User.Role.APPLICANT
        )
        
        self.application = Application.objects.create(
            applicant=self.applicant,
            title='Test Application',
            call_program='Test Program',
            abstract='Test abstract',
            requested_amount=100000,
            status=ApplicationStatus.DRAFT
        )
    
    def test_valid_transition(self):
        """Test valid state transition."""
        sm = ApplicationStateMachine(self.application)
        
        assert sm.can_transition_to(ApplicationStatus.SUBMITTED)
        
        sm.transition_to(ApplicationStatus.SUBMITTED, actor=self.applicant)
        
        assert self.application.status == ApplicationStatus.SUBMITTED
        assert self.application.submitted_at is not None
    
    def test_invalid_transition(self):
        """Test invalid state transition."""
        sm = ApplicationStateMachine(self.application)
        
        assert not sm.can_transition_to(ApplicationStatus.APPROVED)
        
        with pytest.raises(StateTransitionError):
            sm.transition_to(ApplicationStatus.APPROVED, actor=self.applicant)
    
    def test_audit_log_creation(self):
        """Test audit log is created on transition."""
        from apps.applications.models import AuditLog
        
        sm = ApplicationStateMachine(self.application)
        sm.transition_to(ApplicationStatus.SUBMITTED, actor=self.applicant, reason='Test submission')
        
        logs = AuditLog.objects.filter(application=self.application)
        assert logs.count() > 0
        
        log = logs.first()
        assert log.action_type == AuditLog.ActionType.STATE_CHANGE
        assert log.actor == self.applicant
