"""
Views for appeals and revision requests.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.users.permissions import applicant_required, admin_required
from .models import Application, Appeal, RevisionRequest


@applicant_required
def file_appeal(request, application_id):
    """File an appeal against rejection."""
    application = get_object_or_404(Application, pk=application_id, applicant=request.user)
    
    if application.status != 'REJECTED':
        messages.error(request, 'Appeals can only be filed for rejected applications.')
        return redirect('applications:detail', pk=application_id)
    
    if request.method == 'POST':
        Appeal.objects.create(
            application=application,
            appellant=request.user,
            reason=request.POST.get('reason'),
            supporting_documents=request.POST.get('supporting_documents', '')
        )
        
        # Update application status
        application.status = 'APPEAL_PENDING'
        application.save()
        
        messages.success(request, 'Appeal filed successfully.')
        return redirect('applications:detail', pk=application_id)
    
    return render(request, 'applications/appeal.html', {
        'application': application
    })


@applicant_required
def view_revision_request(request, application_id):
    """View revision request details."""
    application = get_object_or_404(Application, pk=application_id, applicant=request.user)
    revision_request = application.revision_requests.filter(status='PENDING').first()
    
    if not revision_request:
        messages.error(request, 'No pending revision request found.')
        return redirect('applications:detail', pk=application_id)
    
    return render(request, 'applications/revision_request.html', {
        'application': application,
        'revision_request': revision_request
    })


@applicant_required
def submit_revision(request, application_id):
    """Submit revised application."""
    application = get_object_or_404(Application, pk=application_id, applicant=request.user)
    revision_request = application.revision_requests.filter(status='PENDING').first()
    
    if not revision_request:
        messages.error(request, 'No pending revision request found.')
        return redirect('applications:detail', pk=application_id)
    
    if request.method == 'POST':
        # Mark revision as completed
        revision_request.status = 'COMPLETED'
        revision_request.completed_at = timezone.now()
        revision_request.applicant_notes = request.POST.get('applicant_notes', '')
        revision_request.save()
        
        # Update application status
        application.status = 'SUBMITTED'
        application.save()
        
        messages.success(request, 'Revision submitted successfully.')
        return redirect('applications:detail', pk=application_id)
    
    return render(request, 'applications/submit_revision.html', {
        'application': application,
        'revision_request': revision_request
    })


@admin_required
def request_revision(request, application_id):
    """Admin: Request revision from applicant."""
    application = get_object_or_404(Application, pk=application_id)
    
    if request.method == 'POST':
        RevisionRequest.objects.create(
            application=application,
            requested_by=request.user,
            changes_required=request.POST.get('changes_required')
        )
        
        # Update application status
        application.status = 'REVISION_REQUESTED'
        application.save()
        
        messages.success(request, 'Revision request sent to applicant.')
        return redirect('applications:detail', pk=application_id)
    
    return render(request, 'applications/request_revision_form.html', {
        'application': application
    })
