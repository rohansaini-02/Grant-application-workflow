"""
Admin configuration for Users app.
Implements comprehensive list views with pagination, filtering, and search.
Shows role-group synchronization status.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User


# Customize Group admin to show related users
class GroupAdmin(admin.ModelAdmin):
    """Enhanced Group admin showing role-based group info."""
    
    list_display = ['name', 'get_user_count', 'get_permissions_count']
    search_fields = ['name']
    filter_horizontal = ['permissions']
    
    def get_user_count(self, obj):
        """Display number of users in this group."""
        return obj.user_set.count()
    get_user_count.short_description = 'Users'
    
    def get_permissions_count(self, obj):
        """Display number of permissions assigned to this group."""
        return obj.permissions.count()
    get_permissions_count.short_description = 'Permissions'
    
    def get_readonly_fields(self, request, obj=None):
        """Make role-based group names read-only."""
        if obj and obj.name in ['Applicants', 'Reviewers', 'Admins']:
            return ['name']
        return []
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of role-based groups."""
        if obj and obj.name in ['Applicants', 'Reviewers', 'Admins']:
            return False
        return super().has_delete_permission(request, obj)


# Re-register Group with custom admin
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with role-based filtering and group display.
    Shows automatic role-group synchronization.
    """
    
    # List display configuration
    list_display = [
        'username',
        'email',
        'get_full_name',
        'role',
        'get_group_name',
        'current_load',
        'is_active',
        'date_joined',
    ]
    
    list_filter = [
        'role',
        'groups',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    ]
    
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'organization',
    ]
    
    # Pagination
    list_per_page = 50
    
    # Fieldsets for detail view
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Group', {
            'fields': ('role', 'get_assigned_group'),
            'description': 'The group is automatically assigned based on the role. '
                          'Permissions assigned to the group will apply to this user.',
        }),
        ('Reviewer Details', {
            'fields': ('expertise_tags', 'current_load'),
            'classes': ('collapse',),
        }),
        ('Additional Information', {
            'fields': ('bio', 'organization', 'phone'),
            'classes': ('collapse',),
        }),
    )
    
    # Add fieldsets for creating new users
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Expertise', {
            'fields': ('role', 'expertise_tags'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ['date_joined', 'last_login', 'get_assigned_group']
    
    # Ordering
    ordering = ['-date_joined']
    
    def get_full_name(self, obj):
        """Display full name."""
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Full Name'
    
    def get_group_name(self, obj):
        """Display the role-based group name."""
        return obj.ROLE_GROUP_MAP.get(obj.role, '-')
    get_group_name.short_description = 'Auto Group'
    
    def get_assigned_group(self, obj):
        """Display the assigned group with permission count."""
        group_name = obj.ROLE_GROUP_MAP.get(obj.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                perm_count = group.permissions.count()
                return f"{group_name} ({perm_count} permissions)"
            except Group.DoesNotExist:
                return f"{group_name} (not created yet)"
        return '-'
    get_assigned_group.short_description = 'Assigned Group'
    
    def save_model(self, request, obj, form, change):
        """
        Override to ensure group sync message is shown.
        """
        super().save_model(request, obj, form, change)
        
        from django.contrib import messages
        group_name = obj.ROLE_GROUP_MAP.get(obj.role)
        if group_name:
            messages.info(
                request, 
                f"User '{obj.username}' has been automatically added to the '{group_name}' group."
            )
