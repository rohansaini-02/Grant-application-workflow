"""
Views for Call for Proposals management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.users.permissions import admin_required
from .models import Call


def call_list(request):
    """Public list of open calls."""
    calls = Call.objects.filter(
        is_open=True,
        deadline__gte=timezone.now()
    ).order_by('deadline')
    
    return render(request, 'calls/list.html', {
        'calls': calls
    })


def call_detail(request, pk):
    """Public call detail page."""
    call = get_object_or_404(Call, pk=pk)
    
    return render(request, 'calls/detail.html', {
        'call': call
    })


@admin_required
def call_create(request):
    """Admin: Create new call."""
    if request.method == 'POST':
        call = Call.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            deadline=request.POST.get('deadline'),
            funding_amount_min=request.POST.get('funding_amount_min') or None,
            funding_amount_max=request.POST.get('funding_amount_max') or None,
            eligibility_criteria=request.POST.get('eligibility_criteria', ''),
            created_by=request.user
        )
        messages.success(request, f'Call "{call.title}" created successfully.')
        return redirect('calls:detail', pk=call.pk)
    
    return render(request, 'calls/create.html')


@admin_required
def call_edit(request, pk):
    """Admin: Edit existing call."""
    call = get_object_or_404(Call, pk=pk)
    
    if request.method == 'POST':
        call.title = request.POST.get('title')
        call.description = request.POST.get('description')
        call.deadline = request.POST.get('deadline')
        call.is_open = request.POST.get('is_open') == 'on'
        call.funding_amount_min = request.POST.get('funding_amount_min') or None
        call.funding_amount_max = request.POST.get('funding_amount_max') or None
        call.eligibility_criteria = request.POST.get('eligibility_criteria', '')
        call.save()
        
        messages.success(request, f'Call "{call.title}" updated successfully.')
        return redirect('calls:detail', pk=call.pk)
    
    return render(request, 'calls/edit.html', {'call': call})
