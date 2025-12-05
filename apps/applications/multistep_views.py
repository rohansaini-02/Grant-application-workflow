"""
Multi-step application form view.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.permissions import applicant_required
from .models import Application, Call, ApplicationVersion, Document
import json


@applicant_required
def apply_multistep(request):
    """Multi-step application form."""
    
    # Get current step from session or default to 1
    step = int(request.session.get('application_step', 1))
    
    # Get call if specified
    call_id = request.GET.get('call') or request.session.get('application_call')
    call = None
    if call_id:
        call = get_object_or_404(Call, pk=call_id)
        request.session['application_call'] = str(call_id)
    
    # Get form data from session
    form_data = request.session.get('application_form_data', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Save current step data
        for key in request.POST:
            if key not in ['csrfmiddlewaretoken', 'action']:
                form_data[key] = request.POST.get(key)
        
        # Handle file uploads
        for key in request.FILES:
            # Store file reference (in real implementation, save to temp location)
            form_data[f'{key}_uploaded'] = request.FILES[key].name
        
        request.session['application_form_data'] = form_data
        
        if action == 'next' and step < 5:
            step += 1
            request.session['application_step'] = step
        elif action == 'previous' and step > 1:
            step -= 1
            request.session['application_step'] = step
        elif action == 'save_draft':
            # Save as draft
            application = _save_application_draft(request, form_data, call)
            messages.success(request, 'Draft saved successfully.')
            return redirect('applications:detail', pk=application.pk)
        elif action == 'submit':
            # Final submission
            application = _save_application_draft(request, form_data, call)
            application.status = 'SUBMITTED'
            application.save()
            
            # Clear session
            request.session.pop('application_step', None)
            request.session.pop('application_form_data', None)
            request.session.pop('application_call', None)
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('applications:detail', pk=application.pk)
    
    return render(request, 'applications/apply_multistep.html', {
        'step': step,
        'form_data': form_data,
        'call': call
    })


def _save_application_draft(request, form_data, call):
    """Helper to save application draft."""
    
    # Parse tags
    tags = []
    if form_data.get('tags'):
        tags = [tag.strip() for tag in form_data.get('tags', '').split(',')]
    
    # Create or update application
    application = Application.objects.create(
        applicant=request.user,
        call=call,
        title=form_data.get('title', ''),
        abstract=form_data.get('abstract', ''),
        requested_amount=form_data.get('requested_amount', 0),
        tags=tags,
        call_program=call.title if call else 'General',
        status='DRAFT'
    )
    
    # Create version with all data
    version_data = {
        'title': form_data.get('title'),
        'abstract': form_data.get('abstract'),
        'tags': tags,
        'requested_amount': form_data.get('requested_amount'),
        'co_investigators': form_data.get('co_investigators', ''),
        'affiliations': form_data.get('affiliations', ''),
        'full_proposal': form_data.get('full_proposal', ''),
        'budget_summary': form_data.get('budget_summary', ''),
    }
    
    ApplicationVersion.objects.create(
        application=application,
        version_number=1,
        data=version_data,
        created_by=request.user,
        change_summary='Initial draft'
    )
    
    return application
