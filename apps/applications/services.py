"""
Services for application management, versioning, and document handling.
"""

from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
import magic
import os
from .models import Application, ApplicationVersion, Document, AuditLog
from .state_machine import create_audit_log


class ApplicationService:
    """Service for application-related operations."""
    
    @staticmethod
    def create_version(application, data, created_by, change_summary=''):
        """
        Create a new version of the application.
        
        Args:
            application: Application instance
            data: Dictionary of application data
            created_by: User creating the version
            change_summary: Summary of changes
        
        Returns:
            Created ApplicationVersion instance
        """
        # Get the latest version number
        latest_version = application.versions.order_by('-version_number').first()
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create new version
        version = ApplicationVersion.objects.create(
            application=application,
            version_number=version_number,
            data=data,
            created_by=created_by,
            change_summary=change_summary
        )
        
        # Create audit log
        create_audit_log(
            action_type=AuditLog.ActionType.UPDATED,
            actor=created_by,
            application=application,
            details={
                'version_number': version_number,
                'change_summary': change_summary
            }
        )
        
        return version
    
    @staticmethod
    def get_version_diff(version1, version2):
        """
        Get differences between two versions.
        
        Args:
            version1: First ApplicationVersion
            version2: Second ApplicationVersion
        
        Returns:
            Dictionary of changes
        """
        return version1.get_diff(version2)


class DocumentService:
    """Service for document upload and validation."""
    
    @staticmethod
    def validate_file(uploaded_file):
        """
        Validate uploaded file for size and MIME type.
        
        Args:
            uploaded_file: Django UploadedFile instance
        
        Returns:
            Tuple (is_valid, error_message)
        """
        # Check file size
        if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size of {max_mb}MB"
        
        # Check MIME type
        mime = magic.from_buffer(uploaded_file.read(2048), mime=True)
        uploaded_file.seek(0)  # Reset file pointer
        
        if mime not in settings.ALLOWED_UPLOAD_TYPES:
            return False, f"File type '{mime}' is not allowed"
        
        return True, mime
    
    @staticmethod
    def upload_document(application, uploaded_file, document_type, uploaded_by, description=''):
        """
        Upload and attach a document to an application.
        
        Args:
            application: Application instance
            uploaded_file: Django UploadedFile instance
            document_type: Document type (Document.DocumentType)
            uploaded_by: User uploading the document
            description: Optional description
        
        Returns:
            Tuple (Document instance or None, error_message or None)
        """
        # Validate file
        is_valid, result = DocumentService.validate_file(uploaded_file)
        if not is_valid:
            return None, result
        
        mime_type = result
        
        # Create document
        document = Document.objects.create(
            application=application,
            document_type=document_type,
            file=uploaded_file,
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            mime_type=mime_type,
            uploaded_by=uploaded_by,
            description=description
        )
        
        # Create audit log
        create_audit_log(
            action_type=AuditLog.ActionType.DOCUMENT_UPLOADED,
            actor=uploaded_by,
            application=application,
            details={
                'document_id': str(document.id),
                'filename': document.filename,
                'document_type': document_type,
                'file_size': uploaded_file.size
            }
        )
        
        return document, None
    
    @staticmethod
    def delete_document(document, deleted_by):
        """
        Delete a document.
        
        Args:
            document: Document instance
            deleted_by: User deleting the document
        """
        application = document.application
        filename = document.filename
        
        # Delete file from storage
        if document.file:
            document.file.delete(save=False)
        
        # Delete document record
        document.delete()
        
        # Create audit log
        create_audit_log(
            action_type=AuditLog.ActionType.DOCUMENT_DELETED,
            actor=deleted_by,
            application=application,
            details={
                'filename': filename
            }
        )
