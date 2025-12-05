"""
Views for reports app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.contrib import messages
from django.utils import timezone
from apps.users.permissions import admin_required
from apps.applications.models import Application
from apps.reviews.models import Review
from .models import Export
from .services import CSVExportService, PDFExportService, ZIPExportService


@admin_required
def admin_dashboard(request):
    """Admin dashboard with analytics."""
    from apps.applications.models import Application
    from apps.reviews.models import ReviewAssignment, Review
    from apps.users.models import User
    from django.db.models import Count, Avg, Q
    
    # Total counts
    total_applications = Application.objects.count()
    total_reviews = Review.objects.filter(status=Review.ReviewStatus.SUBMITTED).count()
    total_reviewers = User.objects.filter(role=User.Role.REVIEWER).count()
    
    # Average score
    avg_score = Review.objects.filter(
        status=Review.ReviewStatus.SUBMITTED
    ).aggregate(Avg('overall_score'))['overall_score__avg'] or 0
    
    # Application statistics by status
    status_distribution = []
    status_counts = Application.objects.values('status').annotate(count=Count('id'))
    for stat in status_counts:
        percentage = (stat['count'] / total_applications * 100) if total_applications > 0 else 0
        status_distribution.append({
            'status': stat['status'],
            'count': stat['count'],
            'percentage': percentage
        })
    
    # Reviewer statistics
    reviewer_stats = []
    reviewers = User.objects.filter(role=User.Role.REVIEWER)
    max_load = max([r.current_load for r in reviewers]) if reviewers else 1
    
    for reviewer in reviewers:
        completed = ReviewAssignment.objects.filter(
            reviewer=reviewer,
            status=ReviewAssignment.AssignmentStatus.COMPLETED
        ).count()
        pending = ReviewAssignment.objects.filter(
            reviewer=reviewer,
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).count()
        
        reviewer_stats.append({
            'name': reviewer.get_full_name(),
            'current_load': reviewer.current_load,
            'completed': completed,
            'pending': pending,
            'load_percentage': (reviewer.current_load / max_load * 100) if max_load > 0 else 0
        })
    
    # Quick stats
    pending_reviews = ReviewAssignment.objects.filter(
        status__in=['ASSIGNED', 'IN_PROGRESS']
    ).count()
    
    overdue_reviews = ReviewAssignment.objects.filter(
        status__in=['ASSIGNED', 'IN_PROGRESS'],
        due_date__lt=timezone.now()
    ).count()
    
    under_review_count = Application.objects.filter(status='UNDER_REVIEW').count()
    approved_count = Application.objects.filter(status='APPROVED').count()
    
    # Recent exports
    recent_exports = Export.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_applications': total_applications,
        'total_reviews': total_reviews,
        'total_reviewers': total_reviewers,
        'avg_score': avg_score,
        'status_distribution': status_distribution,
        'reviewer_stats': reviewer_stats,
        'pending_reviews': pending_reviews,
        'overdue_reviews': overdue_reviews,
        'under_review_count': under_review_count,
        'approved_count': approved_count,
        'recent_exports': recent_exports,
    }
    
    return render(request, 'reports/dashboard.html', context)


@admin_required
def export_applications(request):
    """Export applications to CSV."""
    applications = Application.objects.all()
    
    export = CSVExportService.export_applications(applications, created_by=request.user)
    
    messages.success(request, f'Export created: {export.filename}')
    return redirect(export.get_download_url())


@admin_required
def export_reviews(request):
    """Export reviews to CSV."""
    reviews = Review.objects.filter(status=Review.ReviewStatus.SUBMITTED)
    
    export = CSVExportService.export_reviews(reviews, created_by=request.user)
    
    messages.success(request, f'Export created: {export.filename}')
    return redirect(export.get_download_url())


@admin_required
def export_feedback_packet(request, application_id):
    """Export feedback packet for an application."""
    application = get_object_or_404(Application, pk=application_id)
    
    export = ZIPExportService.create_feedback_package(application, created_by=request.user)
    
    messages.success(request, f'Feedback packet created: {export.filename}')
    return redirect(export.get_download_url())


@login_required
def download_export(request, access_token):
    """Download export file using access token."""
    export = get_object_or_404(Export, access_token=access_token)
    
    if export.is_expired():
        raise Http404("Export has expired")
    
    # Increment download count
    export.increment_download_count()
    
    # Serve file
    import os
    if not os.path.exists(export.file_path):
        raise Http404("File not found")
    
    response = FileResponse(open(export.file_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{export.filename}"'
    
    return response
