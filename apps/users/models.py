"""
User models for Grant Application Workflow.
Implements role-based user system with APPLICANT, REVIEWER, and ADMIN roles.
Includes automatic synchronization between roles and Django Groups.
"""

from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.core.validators import MinValueValidator


class User(AbstractUser):
    """
    Extended User model with role-based access control.
    Automatically syncs role with corresponding Django Group.
    """
    
    class Role(models.TextChoices):
        APPLICANT = 'APPLICANT', 'Applicant'
        REVIEWER = 'REVIEWER', 'Reviewer'
        ADMIN = 'ADMIN', 'Admin'
    
    # Mapping from role to group name
    ROLE_GROUP_MAP = {
        'APPLICANT': 'Applicants',
        'REVIEWER': 'Reviewers',
        'ADMIN': 'Admins',
    }
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.APPLICANT,
        help_text="User's role in the system. Changing this will automatically update group membership."
    )
    
    expertise_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="List of expertise areas for reviewer matching (e.g., ['biology', 'chemistry'])"
    )
    
    current_load = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current number of active review assignments"
    )
    
    bio = models.TextField(
        blank=True,
        help_text="User biography or description"
    )
    
    organization = models.CharField(
        max_length=255,
        blank=True,
        help_text="User's affiliated organization"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number"
    )
    
    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['current_load']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        """
        Override save to sync role with corresponding Django Group.
        """
        # Check if this is a new user or role has changed
        is_new = self.pk is None
        old_role = None
        
        if not is_new:
            try:
                old_user = User.objects.get(pk=self.pk)
                old_role = old_user.role
            except User.DoesNotExist:
                pass
        
        # Save the user first
        super().save(*args, **kwargs)
        
        # Sync group membership if role changed or is new user
        if is_new or old_role != self.role:
            self._sync_role_group()
    
    def _sync_role_group(self):
        """
        Synchronize the user's group membership based on their role.
        Removes user from all role-based groups and adds to the correct one.
        """
        # Get all role-based group names
        role_group_names = list(self.ROLE_GROUP_MAP.values())
        
        # Remove user from all role-based groups
        role_groups = Group.objects.filter(name__in=role_group_names)
        for group in role_groups:
            group.user_set.remove(self)
        
        # Add user to the correct group based on their role
        group_name = self.ROLE_GROUP_MAP.get(self.role)
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            group.user_set.add(self)
    
    def is_applicant(self):
        """Check if user is an applicant."""
        return self.role == self.Role.APPLICANT
    
    def is_reviewer(self):
        """Check if user is a reviewer."""
        return self.role == self.Role.REVIEWER
    
    def is_admin_user(self):
        """Check if user is an admin (not to be confused with Django's is_staff)."""
        return self.role == self.Role.ADMIN
    
    def increment_load(self):
        """Increment reviewer's current load."""
        self.current_load += 1
        self.save(update_fields=['current_load'])
    
    def decrement_load(self):
        """Decrement reviewer's current load."""
        if self.current_load > 0:
            self.current_load -= 1
            self.save(update_fields=['current_load'])
    
    def get_role_permissions(self):
        """
        Get all permissions from the user's role-based group.
        Returns a set of permission codenames.
        """
        group_name = self.ROLE_GROUP_MAP.get(self.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                return set(group.permissions.values_list('codename', flat=True))
            except Group.DoesNotExist:
                pass
        return set()
    
    def has_role_permission(self, perm_codename):
        """
        Check if user has a specific permission through their role-based group.
        """
        return perm_codename in self.get_role_permissions()
