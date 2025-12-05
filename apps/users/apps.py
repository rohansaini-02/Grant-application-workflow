"""
Users app configuration.
Creates role-based groups on app startup.
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_role_groups(sender, **kwargs):
    """
    Create default role-based groups after migrations.
    This ensures the groups exist when the app starts.
    """
    from django.contrib.auth.models import Group
    
    role_groups = ['Applicants', 'Reviewers', 'Admins']
    
    for group_name in role_groups:
        Group.objects.get_or_create(name=group_name)
    
    print(f"✓ Role-based groups created/verified: {', '.join(role_groups)}")


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users'
    
    def ready(self):
        """
        Connect signal to create groups after migrations.
        """
        post_migrate.connect(create_role_groups, sender=self)
