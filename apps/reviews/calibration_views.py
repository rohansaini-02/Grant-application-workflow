"""
Views for calibration sessions.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.permissions import reviewer_required, admin_required
from .models import CalibrationSession, CalibrationScore


@reviewer_required
def calibration_list(request):
    """List calibration sessions for reviewer."""
    sessions = CalibrationSession.objects.filter(
        participants=request.user
    ).order_by('-session_date')
    
    return render(request, 'reviews/calibration_list.html', {
        'sessions': sessions
    })


@reviewer_required
def calibration_session(request, pk):
    """Calibration session scoring interface."""
    session = get_object_or_404(CalibrationSession, pk=pk)
    
    if request.user not in session.participants.all():
        messages.error(request, 'You are not a participant in this session.')
        return redirect('reviews:calibration_list')
    
    # Get or create reviewer's score
    score, created = CalibrationScore.objects.get_or_create(
        session=session,
        reviewer=request.user
    )
    
    if request.method == 'POST':
        # Save scores
        scores = {}
        for criterion in session.rubric.criteria.all():
            score_key = f'score_{criterion.id}'
            if score_key in request.POST:
                scores[str(criterion.id)] = int(request.POST[score_key])
        
        score.scores = scores
        score.comments = request.POST.get('comments', '')
        
        # Calculate overall score
        score.overall_score = session.rubric.calculate_weighted_score(scores)
        score.save()
        
        messages.success(request, 'Calibration scores saved.')
        return redirect('reviews:calibration_session', pk=pk)
    
    criteria = session.rubric.criteria.all()
    all_scores = session.get_participant_scores()
    
    return render(request, 'reviews/calibration_session.html', {
        'session': session,
        'score': score,
        'criteria': criteria,
        'all_scores': all_scores
    })
