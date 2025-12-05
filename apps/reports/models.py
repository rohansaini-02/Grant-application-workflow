"""
Models for reports and exports.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid


class Export(models.Model):
    """
    Track generated exports with time-limited access.
    """
    
    class ExportType(models.TextChoices):
        CSV_SUMMARY = 'CSV_SUMMARY', 'CSV Summary'
        FEEDBACK_PACKET = 'FEEDBACK_PACKET', 'Feedback Packet (ZIP)'
        AUDIT_LOG = 'AUDIT_LOG', 'Audit Log'
        ANALYTICS = 'ANALYTICS', 'Analytics Report'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    export_type = models.CharField(
        max_length=30,
        choices=ExportType.choices
    )
    
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Access token for time-limited downloads
    access_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} ({self.get_export_type_display()})"
    
    def is_expired(self):
        """Check if export has expired."""
        return timezone.now() > self.expires_at
    
    def get_download_url(self):
        """Get time-limited download URL."""
        return f"/reports/download/{self.access_token}/"
    
    def increment_download_count(self):
        """Increment download counter."""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    @classmethod
    def create_export(cls, export_type, filename, file_path, created_by, expiry_hours=24):
        """
        Create a new export with expiration.
        
        Args:
            export_type: Type of export
            filename: Display filename
            file_path: Path to file on disk
            created_by: User who created the export
            expiry_hours: Hours until expiration
        
        Returns:
            Export instance
        """
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        
        return cls.objects.create(
            export_type=export_type,
            filename=filename,
            file_path=file_path,
            created_by=created_by,
            expires_at=expires_at
        )
