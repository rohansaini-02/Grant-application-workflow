"""
Admin configuration for Reviews app.
Implements comprehensive list views with pagination, filtering, and search.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Rubric, Criterion, ReviewAssignment, Review, COIFlag,
    CalibrationSession, CalibrationScore
)


class CriterionInline(admin.TabularInline):
    """Inline editing of criteria within rubric."""
    model = Criterion
    extra = 1
    fields = ['name', 'description', 'weight', 'min_score', 'max_score', 'is_required', 'order']
    ordering = ['order']


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    """
    Admin for Rubric model with inline criteria editing.
    """
    
    list_display = ['name', 'criteria_count', 'total_weight', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_per_page = 50
    
    inlines = [CriterionInline]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def criteria_count(self, obj):
        """Display number of criteria."""
        return obj.criteria.count()
    criteria_count.short_description = 'Criteria Count'
    
    def total_weight(self, obj):
        """Display total weight."""
        return obj.get_total_weight()
    total_weight.short_description = 'Total Weight'


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    """Admin for individual criteria."""
    
    list_display = ['name', 'rubric', 'weight', 'min_score', 'max_score', 'is_required', 'order']
    list_filter = ['rubric', 'is_required']
    search_fields = ['name', 'description', 'rubric__name']
    list_per_page = 50
    ordering = ['rubric', 'order']


@admin.register(ReviewAssignment)
class ReviewAssignmentAdmin(admin.ModelAdmin):
    """
    Admin for ReviewAssignment with comprehensive filtering.
    """
    
    list_display = [
        'application_link',
        'reviewer_link',
        'status_badge',
        'is_blinded',
        'assigned_date',
        'due_date',
        'is_overdue_indicator',
    ]
    
    list_filter = [
        'status',
        'is_blinded',
        'assigned_date',
        'due_date',
        'rubric',
    ]
    
    search_fields = [
        'application__title',
        'reviewer__username',
        'reviewer__first_name',
        'reviewer__last_name',
        'reviewer__email',
    ]
    
    list_per_page = 50
    
    readonly_fields = ['assigned_date']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('application', 'reviewer', 'rubric', 'assigned_by')
        }),
        ('Status & Blinding', {
            'fields': ('status', 'is_blinded')
        }),
        ('Deadlines', {
            'fields': ('assigned_date', 'due_date')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['bulk_unblind', 'send_reminders']
    
    def application_link(self, obj):
        """Display application with link."""
        url = reverse('admin:applications_application_change', args=[obj.application.id])
        return format_html('<a href="{}">{}</a>', url, obj.application.title[:50])
    application_link.short_description = 'Application'
    
    def reviewer_link(self, obj):
        """Display reviewer with link."""
        url = reverse('admin:users_user_change', args=[obj.reviewer.id])
        return format_html('<a href="{}">{}</a>', url, obj.reviewer.get_full_name() or obj.reviewer.username)
    reviewer_link.short_description = 'Reviewer'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'ASSIGNED': '#007bff',
            'IN_PROGRESS': '#ffc107',
            'COMPLETED': '#28a745',
            'DECLINED': '#dc3545',
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
    
    def bulk_unblind(self, request, queryset):
        """Bulk action to unblind selected assignments."""
        count = queryset.update(is_blinded=False)
        self.message_user(request, f'{count} assignments unblinded.')
    bulk_unblind.short_description = 'Unblind selected assignments'
    
    def send_reminders(self, request, queryset):
        """Send reminder emails to reviewers."""
        # This would integrate with notifications app
        self.message_user(request, f'Reminder functionality will be implemented in notifications app.')
    send_reminders.short_description = 'Send reminder emails'
    
    def save_model(self, request, obj, form, change):
        """Override save to send notifications."""
        super().save_model(request, obj, form, change)
        
        if not change:  # Only for new assignments
            from apps.notifications.services import NotificationService
            NotificationService.notify_review_assigned(obj)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin for Review model.
    """
    
    list_display = [
        'reviewer_name',
        'application_title',
        'status',
        'overall_score_display',
        'submitted_at',
        'updated_at',
    ]
    
    list_filter = [
        'status',
        'submitted_at',
        'overall_score',
    ]
    
    search_fields = [
        'assignment__reviewer__username',
        'assignment__reviewer__first_name',
        'assignment__reviewer__last_name',
        'assignment__application__title',
    ]
    
    list_per_page = 50
    
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'overall_score']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('assignment',)
        }),
        ('Scores', {
            'fields': ('scores', 'overall_score')
        }),
        ('Comments', {
            'fields': ('strengths', 'weaknesses', 'recommendation')
        }),
        ('Confidential', {
            'fields': ('confidential_comments',),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at', 'submitted_at')
        }),
    )
    
    def reviewer_name(self, obj):
        """Display reviewer name."""
        return obj.assignment.reviewer.get_full_name() or obj.assignment.reviewer.username
    reviewer_name.short_description = 'Reviewer'
    
    def application_title(self, obj):
        """Display application title."""
        return obj.assignment.application.title[:50]
    application_title.short_description = 'Application'
    
    def overall_score_display(self, obj):
        """Display overall score with color coding."""
        if obj.overall_score is None:
            return '-'
        
        score = float(obj.overall_score)
        if score >= 80:
            color = '#28a745'  # Green
        elif score >= 60:
            color = '#ffc107'  # Yellow
        else:
            color = '#dc3545'  # Red
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            score
        )
    overall_score_display.short_description = 'Overall Score'


@admin.register(COIFlag)
class COIFlagAdmin(admin.ModelAdmin):
    """
    Admin for COI flags.
    """
    
    list_display = [
        'reviewer_link',
        'application_link',
        'coi_type',
        'declared_at',
        'is_resolved',
        'resolved_by',
    ]
    
    list_filter = [
        'coi_type',
        'is_resolved',
        'declared_at',
    ]
    
    search_fields = [
        'reviewer__username',
        'reviewer__first_name',
        'reviewer__last_name',
        'application__title',
        'description',
    ]
    
    list_per_page = 50
    
    readonly_fields = ['declared_at', 'resolved_at']
    
    fieldsets = (
        ('COI Details', {
            'fields': ('reviewer', 'application', 'coi_type', 'description', 'declared_at')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
    )
    
    actions = ['mark_resolved']
    
    def reviewer_link(self, obj):
        """Display reviewer with link."""
        url = reverse('admin:users_user_change', args=[obj.reviewer.id])
        return format_html('<a href="{}">{}</a>', url, obj.reviewer.get_full_name() or obj.reviewer.username)
    reviewer_link.short_description = 'Reviewer'
    
    def application_link(self, obj):
        """Display application with link."""
        url = reverse('admin:applications_application_change', args=[obj.application.id])
        return format_html('<a href="{}">{}</a>', url, obj.application.title[:50])
    application_link.short_description = 'Application'
    
    def mark_resolved(self, request, queryset):
        """Mark selected COI flags as resolved."""
        for coi in queryset.filter(is_resolved=False):
            coi.resolve(resolved_by=request.user, resolution_notes='Resolved via admin action')
        self.message_user(request, f'{queryset.count()} COI flags marked as resolved.')
    mark_resolved.short_description = 'Mark as resolved'


@admin.register(CalibrationSession)
class CalibrationSessionAdmin(admin.ModelAdmin):
    """Admin for Calibration Sessions."""
    
    list_display = ['name', 'session_date', 'example_application', 'consensus_score', 'is_completed']
    list_filter = ['is_completed', 'session_date']
    search_fields = ['name', 'description', 'example_application__title']
    list_per_page = 50
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['participants']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('name', 'description', 'session_date', 'example_application', 'rubric')
        }),
        ('Participants', {
            'fields': ('participants',)
        }),
        ('Consensus', {
            'fields': ('consensus_score', 'consensus_scores_detail', 'is_completed')
        }),
        ('Discussion', {
            'fields': ('discussion_notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CalibrationScore)
class CalibrationScoreAdmin(admin.ModelAdmin):
    """Admin for Calibration Scores."""
    
    list_display = ['session', 'reviewer', 'overall_score', 'submitted_at']
    list_filter = ['session', 'submitted_at']
    search_fields = ['session__name', 'reviewer__username', 'reviewer__first_name', 'reviewer__last_name']
    list_per_page = 50
    readonly_fields = ['submitted_at']
