"""
Cron tasks for reports generation.
"""

from django.utils import timezone
from apps.applications.models import Application
from apps.reviews.models import Review
from .services import CSVExportService


def generate_nightly_reports():
    """
    Generate nightly summary reports.
    Runs daily via django-crontab.
    """
    print(f"[{timezone.now()}] Generating nightly reports...")
    
    # Export all applications
    applications = Application.objects.all()
    
    # Create system user for automated exports (or use first admin)
    from apps.users.models import User
    admin_user = User.objects.filter(role=User.Role.ADMIN).first()
    
    if admin_user:
        export = CSVExportService.export_applications(applications, created_by=admin_user)
        print(f"[{timezone.now()}] Created nightly application export: {export.filename}")
    
    print(f"[{timezone.now()}] Nightly reports completed.")
