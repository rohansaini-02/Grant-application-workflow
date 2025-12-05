"""
Admin configuration for Applications app.
Implements comprehensive list views with pagination, filtering, and search.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Application, ApplicationVersion, Document, DeadlineRule, AuditLog, 
    ApplicationStatus, Call, Appeal, RevisionRequest
)
from .state_machine import ApplicationStateMachine, StateTransitionError


class ApplicationVersionInline(admin.TabularInline):
    """Inline display of application versions."""
    model = ApplicationVersion
    extra = 0
    readonly_fields = ['version_number', 'created_at', 'created_by', 'change_summary']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class DocumentInline(admin.TabularInline):
    """Inline display of application documents."""
    model = Document
    extra = 0
    readonly_fields = ['filename', 'file_size', 'mime_type', 'uploaded_at', 'uploaded_by']
    fields = ['document_type', 'filename', 'file_size', 'uploaded_at', 'description']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """
    Comprehensive admin for Application model.
    """
    
    # List display
    list_display = [
        'title',
        'applicant_link',
        'status_badge',
        'requested_amount',
        'created_at',
        'deadline',
        'is_overdue_indicator',
    ]
    
    list_filter = [
        'status',
        'created_at',
        'submitted_at',
        'deadline',
        'call_program',
    ]
    
    search_fields = [
        'title',
        'applicant__username',
        'applicant__email',
        'applicant__first_name',
        'applicant__last_name',
        'id',
        'abstract',
    ]
    
    # Pagination
    list_per_page = 50
    
    # Detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'applicant', 'call_program', 'abstract')
        }),
        ('Financial', {
            'fields': ('requested_amount',)
        }),
        ('Status & Workflow', {
            'fields': ('status', 'submitted_at', 'deadline')
        }),
        ('Metadata', {
            'fields': ('tags', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'submitted_at']
    
    inlines = [DocumentInline, ApplicationVersionInline]
    
    # Ordering
    ordering = ['-created_at']
    
    # Actions
    actions = ['transition_to_in_triage', 'transition_to_assigned', 'export_selected']
    
    def applicant_link(self, obj):
        """Display applicant with link to user admin."""
        url = reverse('admin:users_user_change', args=[obj.applicant.id])
        return format_html('<a href="{}">{}</a>', url, obj.applicant.get_full_name() or obj.applicant.username)
    applicant_link.short_description = 'Applicant'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'DRAFT': '#6c757d',
            'SUBMITTED': '#007bff',
            'IN_TRIAGE': '#17a2b8',
            'ASSIGNED': '#ffc107',
            'UNDER_REVIEW': '#fd7e14',
            'REVIEWED': '#20c997',
            'DECISION_PENDING': '#6f42c1',
            'APPROVED': '#28a745',
            'REJECTED': '#dc3545',
            'REVISION_REQUESTED': '#e83e8c',
            'UNDER_REVISION': '#fd7e14',
            'APPEAL_PENDING': '#6610f2',
            'APPEAL_REVIEWED': '#6f42c1',
            'ARCHIVED': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def is_overdue_indicator(self, obj):
        """Display overdue indicator."""
        if obj.is_overdue():
            return format_html('<span style="color: red; font-weight: bold;">⚠ OVERDUE</span>')
        return '-'
    is_overdue_indicator.short_description = 'Overdue'
    
    def transition_to_in_triage(self, request, queryset):
        """Bulk action to transition applications to IN_TRIAGE."""
        count = 0
        for app in queryset:
            try:
                sm = ApplicationStateMachine(app)
                sm.transition_to(ApplicationStatus.IN_TRIAGE, actor=request.user, reason='Bulk admin action')
                count += 1
            except StateTransitionError:
                pass
        self.message_user(request, f'{count} applications transitioned to In Triage.')
    transition_to_in_triage.short_description = 'Transition to In Triage'
    
    def transition_to_assigned(self, request, queryset):
        """Bulk action to transition applications to ASSIGNED."""
        count = 0
        for app in queryset:
            try:
                sm = ApplicationStateMachine(app)
                sm.transition_to(ApplicationStatus.ASSIGNED, actor=request.user, reason='Bulk admin action')
                count += 1
            except StateTransitionError:
                pass
        self.message_user(request, f'{count} applications transitioned to Assigned.')
    transition_to_assigned.short_description = 'Transition to Assigned'
    
    def export_selected(self, request, queryset):
        """Export selected applications."""
        # This would integrate with the reports app
        self.message_user(request, f'Export functionality will be implemented in reports app.')
    export_selected.short_description = 'Export selected applications'


@admin.register(ApplicationVersion)
class ApplicationVersionAdmin(admin.ModelAdmin):
    """Admin for application versions."""
    
    list_display = ['application', 'version_number', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['application__title', 'change_summary']
    list_per_page = 50
    readonly_fields = ['application', 'version_number', 'data', 'created_at', 'created_by']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin for documents."""
    
    list_display = ['filename', 'application', 'document_type', 'file_size_display', 'uploaded_at', 'uploaded_by']
    list_filter = ['document_type', 'uploaded_at', 'mime_type']
    search_fields = ['filename', 'application__title', 'description']
    list_per_page = 50
    readonly_fields = ['file_size', 'mime_type', 'uploaded_at', 'uploaded_by']
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = 'File Size'


@admin.register(DeadlineRule)
class DeadlineRuleAdmin(admin.ModelAdmin):
    """Admin for deadline rules."""
    
    list_display = ['name', 'auto_escalate', 'escalation_status', 'is_active']
    list_filter = ['is_active', 'auto_escalate']
    search_fields = ['name', 'description']
    list_per_page = 50


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin for audit logs with comprehensive filtering.
    """
    
    list_display = ['timestamp', 'actor', 'action_type', 'application_link', 'details_preview']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['actor__username', 'application__title', 'details']
    list_per_page = 50
    readonly_fields = ['actor', 'application', 'action_type', 'details', 'timestamp', 'ip_address']
    
    # Ordering
    ordering = ['-timestamp']
    
    def application_link(self, obj):
        """Display application with link."""
        if obj.application:
            url = reverse('admin:applications_application_change', args=[obj.application.id])
            return format_html('<a href="{}">{}</a>', url, obj.application.title)
        return '-'
    application_link.short_description = 'Application'
    
    def details_preview(self, obj):
        """Display preview of details."""
        details_str = str(obj.details)
        if len(details_str) > 50:
            return details_str[:50] + '...'
        return details_str
    details_preview.short_description = 'Details'
    
    def has_add_permission(self, request):
        """Audit logs are append-only, no manual additions."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs cannot be deleted."""
        return False
    
    # Export action
    actions = ['export_audit_logs']
    
    def export_audit_logs(self, request, queryset):
        """Export audit logs to CSV."""
        # This would integrate with the reports app
        self.message_user(request, f'Export functionality will be implemented in reports app.')
    export_audit_logs.short_description = 'Export audit logs'


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    """Admin for Call for Proposals."""
    
    list_display = ['title', 'deadline', 'is_open', 'created_at', 'created_by']
    list_filter = ['is_open', 'deadline', 'created_at']
    search_fields = ['title', 'description']
    list_per_page = 50
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'deadline', 'is_open')
        }),
        ('Funding', {
            'fields': ('funding_amount_min', 'funding_amount_max')
        }),
        ('Eligibility', {
            'fields': ('eligibility_criteria',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    """Admin for Appeals."""
    
    list_display = ['application', 'appellant', 'status', 'filed_at', 'reviewed_at']
    list_filter = ['status', 'filed_at', 'reviewed_at']
    search_fields = ['application__title', 'appellant__username', 'reason']
    list_per_page = 50
    readonly_fields = ['filed_at', 'reviewed_at']
    
    fieldsets = (
        ('Appeal Information', {
            'fields': ('application', 'appellant', 'reason', 'supporting_documents')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'outcome')
        }),
    )


@admin.register(RevisionRequest)
class RevisionRequestAdmin(admin.ModelAdmin):
    """Admin for Revision Requests."""
    
    list_display = ['application', 'requested_by', 'status', 'requested_at', 'completed_at']
    list_filter = ['status', 'requested_at', 'completed_at']
    search_fields = ['application__title', 'changes_required']
    list_per_page = 50
    readonly_fields = ['requested_at', 'completed_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('application', 'requested_by', 'changes_required')
        }),
        ('Status', {
            'fields': ('status', 'requested_at', 'completed_at', 'applicant_notes')
        }),
    )
