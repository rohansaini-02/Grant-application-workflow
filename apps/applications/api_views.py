"""
API views for applications app.
"""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Application
from django.db.models import Q


class ApplicationListView(generics.ListAPIView):
    """List applications via API."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin_user():
            return Application.objects.all()
        elif user.is_applicant():
            return Application.objects.filter(applicant=user)
        elif user.is_reviewer():
            return Application.objects.filter(review_assignments__reviewer=user).distinct()
        
        return Application.objects.none()


class ApplicationDetailView(generics.RetrieveAPIView):
    """Get application details via API."""
    permission_classes = [IsAuthenticated]
    queryset = Application.objects.all()
