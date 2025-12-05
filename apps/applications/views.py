"""
Views for applications app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from apps.users.permissions import can_view_application, can_edit_application, applicant_required
from .models import Application, ApplicationVersion, Document
from .state_machine import ApplicationStateMachine, StateTransitionError
from .services import ApplicationService, DocumentService


@login_required
def application_list(request):
    """List applications based on user role."""
    user = request.user
    
    if user.is_admin_user():
        applications = Application.objects.all()
    elif user.is_applicant():
        applications = Application.objects.filter(applicant=user)
    elif user.is_reviewer():
        # Show applications assigned to this reviewer
        applications = Application.objects.filter(
            review_assignments__reviewer=user
        ).distinct()
    else:
        applications = Application.objects.none()
    
    applications = applications.order_by('-created_at')
    
    return render(request, 'applications/list.html', {
        'applications': applications
    })


@login_required
def application_detail(request, pk):
    """View application details."""
    application = get_object_or_404(Application, pk=pk)
    
    if not can_view_application(request.user, application):
        raise Http404("Application not found")
    
    versions = application.versions.all()[:5]
    documents = application.documents.all()
    
    return render(request, 'applications/detail.html', {
        'application': application,
        'versions': versions,
        'documents': documents,
        'can_edit': can_edit_application(request.user, application)
    })


@applicant_required
def application_create(request):
    """Create new application."""
    if request.method == 'POST':
        # Simplified form handling - in production use ModelForm
        title = request.POST.get('title')
        call_program = request.POST.get('call_program')
        abstract = request.POST.get('abstract')
        requested_amount = request.POST.get('requested_amount')
        
        application = Application.objects.create(
            applicant=request.user,
            title=title,
            call_program=call_program,
            abstract=abstract,
            requested_amount=requested_amount
        )
        
        messages.success(request, 'Application created successfully.')
        return redirect('applications:detail', pk=application.pk)
    
    return render(request, 'applications/create.html')


@login_required
def application_edit(request, pk):
    """Edit application."""
    application = get_object_or_404(Application, pk=pk)
    
    if not can_edit_application(request.user, application):
        messages.error(request, 'You cannot edit this application.')
        return redirect('applications:detail', pk=pk)
    
    if request.method == 'POST':
        application.title = request.POST.get('title')
        application.abstract = request.POST.get('abstract')
        application.requested_amount = request.POST.get('requested_amount')
        application.save()
        
        messages.success(request, 'Application updated successfully.')
        return redirect('applications:detail', pk=pk)
    
    return render(request, 'applications/edit.html', {'application': application})


@login_required
def application_submit(request, pk):
    """Submit application."""
    application = get_object_or_404(Application, pk=pk)
    
    if not can_edit_application(request.user, application):
        messages.error(request, 'You cannot submit this application.')
        return redirect('applications:detail', pk=pk)
    
    try:
        sm = ApplicationStateMachine(application)
        sm.transition_to('SUBMITTED', actor=request.user, reason='Applicant submission')
        
        # Send notification
        from apps.notifications.services import NotificationService
        NotificationService.notify_application_submitted(application)
        NotificationService.notify_admin_application_submitted(application)
        
        messages.success(request, 'Application submitted successfully.')
    except StateTransitionError as e:
        messages.error(request, str(e))
    
    return redirect('applications:detail', pk=pk)


@login_required
def version_history(request, pk):
    """View version history."""
    application = get_object_or_404(Application, pk=pk)
    
    if not can_view_application(request.user, application):
        raise Http404("Application not found")
    
    versions = application.versions.all()
    
    return render(request, 'applications/version_history.html', {
        'application': application,
        'versions': versions
    })


@login_required
def document_upload(request, pk):
    """Upload document."""
    application = get_object_or_404(Application, pk=pk)
    
    if not can_edit_application(request.user, application):
        messages.error(request, 'You cannot upload documents to this application.')
        return redirect('applications:detail', pk=pk)
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        document_type = request.POST.get('document_type', 'OTHER')
        
        document, error = DocumentService.upload_document(
            application=application,
            uploaded_file=uploaded_file,
            document_type=document_type,
            uploaded_by=request.user
        )
        
        if document:
            messages.success(request, 'Document uploaded successfully.')
        else:
            messages.error(request, error)
    
    return redirect('applications:detail', pk=pk)


@login_required
def document_delete(request, doc_id):
    """Delete document."""
    document = get_object_or_404(Document, pk=doc_id)
    application = document.application
    
    if not can_edit_application(request.user, application):
        messages.error(request, 'You cannot delete this document.')
        return redirect('applications:detail', pk=application.pk)
    
    DocumentService.delete_document(document, deleted_by=request.user)
    messages.success(request, 'Document deleted successfully.')
    
    return redirect('applications:detail', pk=application.pk)
