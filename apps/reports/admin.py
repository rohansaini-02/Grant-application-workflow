"""
Admin configuration for Reports app.
"""

from django.contrib import admin
from .models import Export


@admin.register(Export)
class ExportAdmin(admin.ModelAdmin):
    """Admin for exports."""
    
    list_display = ['filename', 'export_type', 'created_by', 'created_at', 'expires_at', 'download_count', 'is_expired_indicator']
    list_filter = ['export_type', 'created_at', 'expires_at']
    search_fields = ['filename', 'created_by__username']
    list_per_page = 50
    readonly_fields = ['created_at', 'access_token', 'download_count']
    
    def is_expired_indicator(self, obj):
        """Display expiration status."""
        from django.utils.html import format_html
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired_indicator.short_description = 'Status'
