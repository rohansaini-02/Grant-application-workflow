"""
Views for reviews app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from apps.users.permissions import reviewer_required, can_review_application
from .models import ReviewAssignment, Review, COIFlag
from apps.applications.models import Application


@login_required
def assignment_list(request):
    """
    List review assignments.
    - Reviewers see only their own assignments
    - Admins see all assignments
    """
    user = request.user
    
    # Admins can see all assignments, reviewers see only their own
    if user.is_admin_user():
        assignments = ReviewAssignment.objects.all().select_related(
            'application', 'rubric', 'reviewer'
        ).order_by('-assigned_date')
        is_admin_view = True
    elif user.is_reviewer():
        assignments = ReviewAssignment.objects.filter(
            reviewer=user
        ).select_related('application', 'rubric').order_by('-assigned_date')
        is_admin_view = False
    else:
        messages.error(request, "You do not have permission to view review assignments.")
        return redirect('dashboard')
    
    pending_count = assignments.filter(status__in=['ASSIGNED', 'IN_PROGRESS']).count()
    completed_count = assignments.filter(status='COMPLETED').count()
    
    return render(request, 'reviews/assignment_list.html', {
        'assignments': assignments,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'is_admin_view': is_admin_view
    })


@reviewer_required
def review_interface(request, pk):
    """Blinded review interface."""
    assignment = get_object_or_404(ReviewAssignment, pk=pk)
    
    if assignment.reviewer != request.user:
        raise Http404("Assignment not found")
    
    # Get or create review
    review, created = Review.objects.get_or_create(assignment=assignment)
    
    if request.method == 'POST':
        # Save scores
        scores = {}
        for criterion in assignment.rubric.criteria.all():
            score_key = f'score_{criterion.id}'
            if score_key in request.POST:
                scores[str(criterion.id)] = int(request.POST[score_key])
        
        review.scores = scores
        review.strengths = request.POST.get('strengths', '')
        review.weaknesses = request.POST.get('weaknesses', '')
        review.recommendation = request.POST.get('recommendation', '')
        review.confidential_comments = request.POST.get('confidential_comments', '')
        
        # Save as draft
        review.save()
        messages.success(request, 'Review saved as draft.')
        return redirect('reviews:review_interface', pk=pk)
    
    criteria = assignment.rubric.criteria.all()
    
    return render(request, 'reviews/review_interface.html', {
        'assignment': assignment,
        'review': review,
        'criteria': criteria,
        'is_blinded': assignment.is_blinded
    })


@reviewer_required
def review_submit(request, pk):
    """Submit review."""
    assignment = get_object_or_404(ReviewAssignment, pk=pk)
    
    if assignment.reviewer != request.user:
        raise Http404("Assignment not found")
    
    try:
        review = assignment.review
        review.submit()
        
        # Notify admins
        from apps.notifications.services import NotificationService
        NotificationService.notify_admin_review_completed(review)
        
        messages.success(request, 'Review submitted successfully.')
    except Review.DoesNotExist:
        messages.error(request, 'Please complete the review before submitting.')
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('reviews:assignment_list')


@reviewer_required
def declare_coi(request, application_id):
    """Declare conflict of interest."""
    application = get_object_or_404(Application, pk=application_id)
    
    if request.method == 'POST':
        coi_type = request.POST.get('coi_type')
        description = request.POST.get('description')
        
        from .services import COIService
        coi_flag = COIService.declare_coi(
            reviewer=request.user,
            application=application,
            coi_type=coi_type,
            description=description
        )
        
        # Notify admins
        from apps.notifications.services import NotificationService
        NotificationService.notify_admin_coi_declared(coi_flag)
        
        messages.success(request, 'Conflict of interest declared.')
        return redirect('reviews:assignment_list')
    
    return render(request, 'reviews/declare_coi.html', {
        'application': application
    })


@reviewer_required
def save_review_score(request, pk):
    """AJAX view to save a single score."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
    assignment = get_object_or_404(ReviewAssignment, pk=pk)
    
    if assignment.reviewer != request.user:
        return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        criterion_id = str(data.get('criterion_id'))
        score = int(data.get('score'))
        
        review, created = Review.objects.get_or_create(assignment=assignment)
        
        # Update scores
        scores = review.scores or {}
        scores[criterion_id] = score
        review.scores = scores
        review.save()
        
        return JsonResponse({'status': 'success', 'overall_score': review.overall_score})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
