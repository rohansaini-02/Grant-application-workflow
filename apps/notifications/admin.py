"""
Admin configuration for Notifications app.
"""

from django.contrib import admin
from .models import Notification, EmailTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for notifications."""
    
    list_display = ['recipient', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'title', 'message']
    list_per_page = 50
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = (
        ('Recipient', {
            'fields': ('recipient',)
        }),
        ('Content', {
            'fields': ('notification_type', 'title', 'message', 'link_url')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at', 'read_at')
        }),
    )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin for email templates."""
    
    list_display = ['name', 'template_type', 'subject', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject', 'body']
    list_per_page = 50
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Email Content', {
            'fields': ('subject', 'body'),
            'description': 'Use {{variable_name}} for template variables like {{applicant_name}}, {{application_title}}, etc.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
